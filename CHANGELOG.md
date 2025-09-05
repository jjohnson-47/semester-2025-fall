# Changelog

All notable changes to this project will be documented in this file.

## 2025-09-04

- Add coverage ratchet (`scripts/ci/coverage_ratchet.py`) with Make target `ratchet` and CI steps.
- Add health check endpoints:
  - `GET /healthz/live` (liveness)
  - `GET /healthz/startup` (readiness)
- Introduce startup module (`dashboard/startup.py`) and move one-off suppress usage there.
- Replace `contextlib.suppress` in request paths with explicit try/except + logging.
- Add CI guard to forbid `contextlib.suppress` outside `dashboard/startup.py`.
- Add golden unit tests for dashboard filters with a stable fixture.
- Enforce test DB statement timeouts using SQLite progress handler (env `TEST_DB_STATEMENT_TIMEOUT_MS`).
- Pre-commit enhancements: add `pyproject-fmt` and a local guard hook option.
- Documentation updates: health checks in README, testing guide for DB timeout.

