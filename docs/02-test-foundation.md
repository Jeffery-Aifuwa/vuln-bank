# Phase 2: Automated Test Foundation

## Phase Objective
Create an automated functional test suite that validates core application operations and authentication boundaries against the live VulnBank runtime, establishing a baseline regression test harness for upcoming CI/CD, container hardening, and remediation phases.

## Plain English Summary
We created an automated functional integration test suite for VulnBank using `pytest` without modifying any application code. We inspected the application's actual routes, payload formats, and token behaviors to write tests that check health availability, registration, authentication boundaries, and money transfers. These tests run against the live application and pass 100%. This gives us a reliable safety net, so when we add CI/CD pipelines, harden container configurations, or patch vulnerabilities in later phases, we can verify instantly that basic banking operations never break.

We now have a robot that checks whether VulnBank still works before and after we make changes.

It can verify things like:

- Is the application alive?
- Can a user register?
- Can a legitimate user authenticate?
- Are unauthorized users blocked?
- Does a valid token work?
- Does a forged token fail?
- Can users perform a normal transfer?

And importantly, we didn't change the application itself to make the tests pass.

## Technical Explanation
Automated integration testing validates software from the perspective of an external HTTP client against real, running backend services (Flask application runtime and PostgreSQL datastore). Tests interact with endpoints over network sockets, asserting HTTP status codes, headers, and JSON responses.

In Phase 2, we implemented an external integration test suite with `pytest` and `requests`. Tests target the live container environment over HTTP (`TARGET_URL`, defaulting to `http://localhost:5000`). Dynamic fixtures generate isolated test credentials via timestamped UUIDs to prevent state collision across subsequent runs. The suite asserts core system behaviors:
1. **Health Surface:** Service availability on `/` and `/healthz`.
2. **Authentication Boundary:** Access control enforcement ensuring unauthenticated users and forged JWTs are denied access to protected endpoints (`/dashboard`), while valid Bearer tokens are authorized.
3. **Banking Operations:** User registration, dynamic dashboard account lookup, and fund transfers between accounts.

## Architecture & Design Decisions
* **Decoupled Black-Box Testing:** Tests run externally via HTTP calls rather than importing Flask's internal test client. This ensures the tests validate actual network sockets, headers, and reverse proxy behaviors identically in local development and cloud CI pipelines.
* **Separation of Functional vs. Security Testing:** Functional tests assert that the application functions under valid, legitimate user parameters. No vulnerability exploits (SQLi, IDOR, XSS) were introduced in this phase; exploit detection belongs strictly to Phases 8, 9, and 10.
* **Dynamic Fixture State:** Test users are dynamically registered per session using UUIDs, avoiding hardcoded database user dependencies or fragile static balance assumptions.
* **Preservation of Existing Repository Tests:** Existing unit tests using mock psycopg2 drivers (`test_runtime_smoke.py`, `test_merchant_payments.py`) were left unchanged.

## What Was Implemented
The following test suite structure was created in `tests/`:

* `tests/conftest.py`: Shared pytest configuration containing:
  * `base_url`: Target URL fixture reading from `TARGET_URL` or falling back to `http://localhost:5000`.
  * `unique_credentials`: Dynamic credential generator producing unique usernames (`user_<uuid>_<timestamp>`).
  * `registered_user`: Fixture that registers an isolated user via `POST /register`.
  * `auth_token`: Fixture that authenticates the user via `POST /login` and returns the JWT Bearer token.
* `tests/test_health.py`: Validates HTTP 200 responses on `/` and `/healthz`.
* `tests/test_auth_boundary.py`: Validates unauthenticated rejection, valid token authorization, forged token rejection, and invalid credential denial on protected endpoints (`/dashboard`).
* `tests/test_banking_operations.py`: Validates user account dashboard rendering and dynamic funds transfers via `POST /transfer` to `ADMIN001`.

## Files & Resources Changed
* Created: `tests/conftest.py`
* Created: `tests/test_health.py`
* Created: `tests/test_auth_boundary.py`
* Created: `tests/test_banking_operations.py`
* Modified: *None (zero application code or configuration changes).*

## Commands Used
```bash
# Host dependency installation
python -m pip install pytest requests

# Execute test suite against live environment
python -m pytest -v tests/test_health.py tests/test_auth_boundary.py tests/test_banking_operations.py