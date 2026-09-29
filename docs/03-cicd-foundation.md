# Phase 3: CI/CD Foundation

## Phase Objective
Establish an automated Continuous Integration pipeline using GitHub Actions to orchestrate automated builds, health polling, functional regression testing, and baseline security scanning (SCA, SAST, Secret Scanning) across all code changes.

## Plain English Summary
We built an automated GitHub Actions CI pipeline that tests and scans VulnBank every time code is pushed. Whenever a commit lands on GitHub, a clean runner automatically spins up the application and database using Docker Compose and runs our automated test suite to ensure no core banking features are broken. At the same time, it runs security scanners to check for leaked secrets, outdated dependencies, and dangerous code patterns, recording those issues without breaking the build. This gives us an automated gatekeeper that catches bugs and catalogs security risks before code ever moves forward.

## Technical Explanation
Continuous Integration enforces deterministic quality and security gates during code ingestion. In Phase 3, we implemented `.github/workflows/ci.yml` using GitHub Actions to run multi-container functional testing alongside shift-left static security scanning.

The workflow is architected into two decoupled, parallel jobs:
1. **`security-scans` (Non-blocking Discovery):**
   * **Secret Scanning (Gitleaks):** Scans the repository history and working tree for exposed credentials, API tokens, and private keys.
   * **Software Composition Analysis (SCA via `pip-audit`):** Evaluates `requirements.txt` against PyPI/OSV advisory databases, outputting detected CVEs into `$GITHUB_STEP_SUMMARY`.
   * **Static Application Security Testing (SAST via Bandit):** Evaluates the Python AST across application routes and utilities, cataloging insecure configurations, hardcoded secrets, and SQL query patterns.
   * *Governance:* Scans operate with `continue-on-error: true`, allowing VulnBank's intentional baseline vulnerabilities to be cataloged transparently without causing artificial CI failures before scheduled remediation phases.
2. **`build-and-test` (Strict Quality Gate):**
   * Provisions an ephemeral `ubuntu-latest` runner with Docker Compose and Python 3.11.
   * Builds and launches `web` and `db` services, using an active shell polling loop against `http://localhost:5000/healthz` to prevent race conditions during PostgreSQL initialization.
   * Executes the Phase 2 `pytest` suite against live container sockets.
   * Operates as a strict zero-tolerance gate (`continue-on-error: false`) that fails the pipeline run if any functional assertion fails. Includes diagnostic container log dumping upon failure and automated teardown (`docker compose down -v`).

## Architecture & Design Decisions
* **Parallel Job Execution:** Running `security-scans` and `build-and-test` concurrently minimizes pipeline duration and isolates functional build failures from security reporting.
* **Non-Blocking Baseline Security Scans:** Because VulnBank is an intentionally vulnerable learning system, security tools will detect genuine flaws (e.g., hardcoded JWT secrets, legacy dependency versions). The scans report detailed findings into GitHub Step Summaries without breaking the build.
* **Strict Integration Test Gate:** The Phase 2 functional test suite operates as a strict blocking gate. If any endpoint or financial workflow regresses, the build fails immediately.
* **Decoupled Fork Management:** The project was forked to `Jeffery-Aifuwa/vuln-bank` to permit automated GitHub Actions workflows without requiring direct write permissions to upstream.

## Files & Resources Changed
* Created: `.github/workflows/ci.yml`
* Created: `docs/03-cicd-foundation.md`
* Tracked/Committed: Phase 2 test suite files under `tests/` (`conftest.py`, `test_health.py`, `test_auth_boundary.py`, `test_banking_operations.py`).

## Commands Used
```bash
# Branch and commit
git checkout -b feature/phase-3-cicd-foundation
git add .github/workflows/ci.yml tests/ docs/
git commit -m "ci: add GitHub Actions workflow, test suite, and project docs"

# Remote configuration and push
git remote rename origin upstream
git remote add origin [https://github.com/Jeffery-Aifuwa/vuln-bank.git](https://github.com/Jeffery-Aifuwa/vuln-bank.git)
git push -u origin feature/phase-3-cicd-foundation
