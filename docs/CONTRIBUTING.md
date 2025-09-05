# Contributing

## Dev setup
- Install uv (https://docs.astral.sh/uv/)
- Sync deps: `uv sync --all-extras`
- Enable pre-commit: `pipx install pre-commit && pre-commit install`

### Guardrails
- Coverage ratchet: run `make cov-xml && make ratchet`. CI fails if coverage drops by >0.5pp and auto-advances on ≥0.5pp improvements.
- Suppress policy: `contextlib.suppress` is forbidden except in `dashboard/startup.py`. CI enforces this and you can enable a pre-commit hook (see below).
- Test DB timeouts: set `TEST_DB_STATEMENT_TIMEOUT_MS=2000` to abort long-running SQLite statements during tests.

## Commands
- `make fmt` – format and autofix with ruff
- `make lint` – ruff lint
- `make typecheck` – mypy scoped
- `make test` – tests (partition with UNIT=1, INTEGRATION=1, SMOKE=1)
- `make cov-xml` – write coverage.xml
- `make build` – run the enhanced pipeline

### Optional pre-commit hooks
Add a local hook to block `contextlib.suppress` usage outside startup:

```yaml
repos:
  - repo: local
    hooks:
      - id: forbid-suppress
        name: forbid suppress outside startup
        entry: bash scripts/ci/forbid_suppress.sh
        language: system
        files: \.py$
```

## Branch + commits
- Use feature branches (`feat/*`, `fix/*`)
- Conventional Commits when possible
