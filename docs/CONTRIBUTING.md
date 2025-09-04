# Contributing

## Dev setup
- Install uv (https://docs.astral.sh/uv/)
- Sync deps: `uv sync --all-extras`
- Enable pre-commit: `pipx install pre-commit && pre-commit install`

## Commands
- `make fmt` – format and autofix with ruff
- `make lint` – ruff lint
- `make typecheck` – mypy scoped
- `make test` – tests (partition with UNIT=1, INTEGRATION=1, SMOKE=1)
- `make cov-xml` – write coverage.xml
- `make build` – run the enhanced pipeline

## Branch + commits
- Use feature branches (`feat/*`, `fix/*`)
- Conventional Commits when possible

