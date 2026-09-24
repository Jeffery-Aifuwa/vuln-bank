# Phase 1: Baseline & Local Validation

## Phase Objective
Establish a documented, verified, and reproducible empirical baseline for the VulnBank application, its backing services, container configuration, database schema, and runtime behaviors prior to introducing automation, infrastructure, or security controls.

## Why the Phase Was Necessary
In legacy system migrations or modern DevSecOps adoption, altering system components without first discovering their actual runtime behavior leads to unresolvable regressions. Establishing an empirical baseline guarantees that:
1. Pre-existing architectural flaws and intentional vulnerabilities are cataloged and not prematurely mistaken for pipeline or infrastructure bugs.
2. Baseline container configurations (user privileges, port exposures, runtime flags) are benchmarked to measure subsequent hardening stages.
3. Database schemas and relational structures are verified from the running engine rather than assumed from external documentation.

## Plain Explanation
We first ran VulnBank without changing anything. We checked how the application, database, and containers work and recorded their current state. We also identified the security and configuration problems that we'll deal with later. This gives us a baseline, so whenever we make a change, we can compare the system against how it worked originally.

## Technical Explanation
Phase 1 validated the running local instance orchestrated via Docker Compose. The environment consists of three interconnected services: an application web tier running Flask on Python 3.9 managed by Werkzeug, a PostgreSQL 13 relational database populated by seed scripts, and an autoheal monitor container. The baseline inspection verified inter-container networking, host-to-container port publishing, runtime user privileges, database table definitions, and HTTP header disclosures.

## Architecture & Design Decisions (Observed Baseline)
* **Web Tier:** Single-container Python Flask runtime executed using a shell wrapper script (`./start.sh`). Running development server engine (`Werkzeug/2.0.1 Python/3.9.25`).
* **Database Tier:** Single-instance PostgreSQL 13 container running with standard environment variables.
* **Autoheal Utility:** An auxiliary monitor container (`willfarrell/autoheal`) querying container health statuses via the Docker engine socket.
* **Network Topology:** Default bridge network facilitating inter-container resolution.
* **Port Bindings:**
  * Application port: `0.0.0.0:5000` (IPv4) and `[::]:5000` (IPv6) published to all interfaces.
  * Database port: `0.0.0.0:5432` (IPv4) and `[::]:5432` (IPv6) exposed publicly on the host.

## What Was Implemented / Observed
No source code, container configurations, or infrastructure components were modified during this phase. All operations were non-destructive read operations to profile runtime behaviors.

### Containers and Services
| Service Name | Container Name | Image | Command | Status | Exposed Ports |
|---|---|---|---|---|---|
| `web` | `vuln-bank-web-1` | `vuln-bank-web` | `./start.sh` | Up (healthy) | `0.0.0.0:5000->5000/tcp`, `[::]:5000->5000/tcp` |
| `db` | `vuln-bank-db-1` | `postgres:13` | `docker-entrypoint.sh postgres` | Up (healthy) | `0.0.0.0:5432->5432/tcp`, `[::]:5432->5432/tcp` |
| `autoheal` | `vuln-bank-autoheal-1` | `willfarrell/autoheal:latest` | `/docker-entrypoint ...` | Up (healthy) | None |

### Database Schemas and Relationships
* **Database Name:** `vulnerable_bank`
* **Table Count:** 10 core relational tables
  * `bill_categories`
  * `bill_payments`
  * `billers`
  * `card_transactions`
  * `loans`
  * `merchant_payments`
  * `merchants`
  * `transactions`
  * `users`
  * `virtual_cards`

* **`users` Table Structure:**
  * `id` (`integer`, Primary Key, auto-incrementing)
  * `username` (`text`, unique, non-null)
  * `password` (`text`, non-null)
  * `account_number` (`text`, unique, non-null)
  * `balance` (`numeric(15,2)`, default: `1000.00`)
  * `is_admin` (`boolean`, default: `false`)
  * `profile_picture` (`text`)
  * `reset_pin` (`text`)
  * `bio` (`text`)
  * `is_suspended` (`boolean`, default: `false`)

## Verification Performed & Results

### 1. Database Connectivity & Relation Verification
* **Command:** `docker compose exec db psql -U postgres -d vulnerable_bank -c "\dt"`
* **Result:** Successfully returned all 10 tables owned by `postgres`.

### 2. User Privilege Assessment
* **Command:** `docker compose exec web whoami`
* **Result:** Returned `root`. The web application process runs under root privileges inside the container.

### 3. Application HTTP Surface
* **Command:** `curl -Iv http://localhost:5000/`
* **Result:**
  * Status: `HTTP/1.0 200 OK`
  * Server disclosure: `Server: Werkzeug/2.0.1 Python/3.9.25`
  * CORS configuration: `Access-Control-Allow-Origin: *`
  * Content length: 56,703 bytes

### 4. Database User Structure
* **Command:** `docker compose exec db psql -U postgres -d vulnerable_bank -c "\d users"`
* **Result:** Confirmed schema definitions, foreign key relationships to `bill_payments`, `loans`, and `virtual_cards`, and column layouts.

## Problems Encountered & Resolutions
* **Issue:** Initial attempts to run `psql` queries failed with `FATAL: database "vulnbank" does not exist` and `database "vuln-bank-db-1" does not exist`.
  * **Cause:** The database was assumed to match the repository name or container hostname.
  * **Resolution:** Executed `psql -U postgres -c "\l"` to enumerate databases directly from the engine; discovered the real name was `vulnerable_bank`.
* **Issue:** Query `SELECT id, username, email, role FROM users LIMIT 5;` failed with `ERROR: column "email" does not exist`.
  * **Cause:** Assumed typical generic schema conventions.
  * **Resolution:** Inspected the exact PostgreSQL table definition via `\d users` to identify real column names (`username`, `account_number`, `is_admin`, `reset_pin`, etc.).

## Security Considerations & Identified Baseline Risks
1. **Container Process Running as Root:** The web application runtime executes as `root`. If an attacker achieves Remote Code Execution (RCE) via web endpoints, they operate with unconstrained privileges inside the container space.
2. **PostgreSQL Exposed to Host Network:** The database container exposes port `5432` on all interfaces (`0.0.0.0`), allowing host-level direct connections to the database.
3. **Hardcoded / Default Credentials:** The default credentials across containers use static plaintext defaults (`POSTGRES_PASSWORD=postgres`, `POSTGRES_USER=postgres`).
4. **Development Server in Execution:** The application serves traffic via Werkzeug's single-threaded development server instead of a production WSGI/ASGI server (such as Gunicorn or uWSGI).
5. **Permissive CORS Header:** The application returns `Access-Control-Allow-Origin: *` globally.
6. **Detailed Server Banners:** Server software, framework, and exact version details (`Werkzeug/2.0.1 Python/3.9.25`) are broadcast in HTTP response headers.

## Important Lessons
* Never assume database names, service names, or database column schemas based on external project documentation or conventions. Always query the running system.
* A healthy container status (`Up (healthy)`) only indicates that health checks pass; it does not indicate whether runtime privileges or networking configurations adhere to security best practices.

## Limitations & Remaining Work
* Intentional web application vulnerabilities (e.g., SQLi, IDOR, XSS, insecure file uploads) remain present and untouched in accordance with project constraints.
* Automated testing does not exist yet to verify that core application flows (login, transfer, balance lookup) continue working when changes are made.

## How This Phase Connects to the Next Phase
Now that the baseline schemas, users table structures, exposed routes, and runtime services are verified, we have the exact foundation needed to build **Phase 2: Automated Test Foundation**. In Phase 2, we will write non-destructive automated functional tests (health checks, login, registration, transaction flows) that assert whether VulnBank functions correctly without manually running ad-hoc terminal commands.
