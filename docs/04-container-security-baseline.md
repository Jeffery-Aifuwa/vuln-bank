# Phase 4: Container Security & Hardening Baseline

## Phase Objective
Audit the container build and runtime posture, transition the web application service from root execution to a least-privilege non-root user, optimize the Docker build context, and integrate automated container vulnerability scanning (Trivy) into the CI pipeline.

## Plain English Summary
We audited the container setup and discovered that VulnBank was previously running with full administrative root privileges and world-writable directories. We hardened the container by creating a dedicated unprivileged user (`appuser` with UID 10001), restricted file ownership across the application, and added a `.dockerignore` file to keep unnecessary files out of the build. We also added Trivy container vulnerability scanning directly into our automated GitHub Actions pipeline. All core banking features still pass our automated tests, but an attacker exploiting an application vulnerability can no longer easily compromise the underlying host system.

## Technical Explanation
Container security requires defense-in-depth across build artifacts and runtime processes. Unhardened containers executing as `root` (UID 0) expose the host to kernel privilege escalation and trivial lateral movement upon remote code execution (RCE).

In Phase 4, we implemented build-time and runtime hardening measures:
1. **Least-Privilege Non-Root Execution:** Created a dedicated system user and group (`appuser:appgroup`, UID/GID 10001) without interactive shell privileges. The container drops root capabilities and runs entirely under this identity.
2. **Scoped Filesystem Permissions:** Directory write access was removed from application source files, scoping write permissions strictly to `/app/static/uploads` with `750` permissions.
3. **Build Context Optimization:** Added `.dockerignore` to exclude local caches, test directories, and git history from image layers.
4. **Automated Image Scanning:** Integrated Trivy into the GitHub Actions CI pipeline to catalog operating system package and dependency CVEs.

## Architecture & Design Decisions
* **Fixed UID/GID Assignment:** Explicitly assigned UID/GID `10001` rather than relying on dynamic system allocation, ensuring consistent permissions across container hosts and volume mounts.
* **Separation of Concerns for File Permissions:** Application source code is owned by `root:root` with read-only/execute access for `appuser`. Only transient storage paths (`static/uploads`) are assigned write ownership.
* **Non-Blocking Trivy Scan in Baseline:** In keeping with our DevSecOps roadmap, Trivy runs in discovery mode (`continue-on-error: true`), logging CVE findings without breaking builds until scheduled remediation phases.
* **Functional Test Gate Preservation:** The Phase 2 integration test suite runs as a mandatory post-build check, guaranteeing that permission tightening does not cause regressions.

## Files & Resources Changed
* Created: `.dockerignore`
* Modified: `Dockerfile` (Added non-root user setup, scoped permissions, `USER appuser`)
* Modified: `.github/workflows/ci.yml` (Added Trivy container image scan step)
* Created: `docs/04-container-security-baseline.md`

## Commands Used
```bash
# Rebuild container image locally
docker compose build --no-cache web
docker compose up -d

# Verify runtime identity
docker compose exec web id
docker compose exec web whoami

# Run integration regression suite
python -m pytest -v tests/test_health.py tests/test_auth_boundary.py tests/test_banking_operations.py

# Commit and push to CI
git checkout -b feature/phase-4-container-hardening
git add Dockerfile .dockerignore .github/workflows/ci.yml docs/04-container-security-baseline.md
git commit -m "feat(container): harden Dockerfile with non-root user and add Trivy scan in CI"
git push -u origin feature/phase-4-container-hardening
