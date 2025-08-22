# Repository Guidelines

## Project Structure & Module Organization
- `scripts/`: build automation (syllabi, schedules, Blackboard); shared utils in `scripts/utils/`.
- `dashboard/`: Flask task dashboard (`app.py`, `templates/`, `tools/`).
- `templates/`: Jinja2 templates for generated outputs.
- `content/`, `profiles/`, `variables/`, `tables/`: source data and configuration.
- `build/`: generated artifacts (ignored by Git).
- `docs/`: reference, API, and examples.

## Build, Test, and Development Commands
- `make help`: list available targets.
- `make init`: sync Python deps with `uv` and validate JSON.
- `make validate`: JSON schema validation for repository data.
- `make all`: full build (calendar → syllabi → schedules → packages).
- `make course COURSE=MATH221`: build a single course.
- `make dash`: run dashboard at `http://127.0.0.1:5055`.
- `make lint` / `make format`: run `pylint` / `black` on `scripts/`.
- `make test`: run `pytest` in `tests/`.
- `make clean` / `make check-deps` / `make dev-server`: housekeeping and preview.

## Coding Style & Naming Conventions
- Python: 4-space indentation, type hints, descriptive names, module/function `snake_case`, class `PascalCase`.
- Organize imports alphabetically and group stdlib/third-party/local.
- Add docstrings for modules, functions, and complex logic; prefer readability over cleverness.
- Tools: `black` for formatting, `pylint` for linting (see Make targets).

## Testing Guidelines
- Framework: `pytest`; place tests under `tests/` with `test_*.py` naming.
- Include unit tests for `scripts/` utilities and integration tests for end-to-end builds.
- Target ≥80% coverage where feasible; mock external I/O and time-dependent logic.
- Validate content frequently with `make validate`; run `make test` before commits.

## Commit & Pull Request Guidelines
- Branches: create feature branches (e.g., `feat/syllabus-pdf`, `fix/validate-edge-cases`).
- Commits: atomic; use Conventional Commits (e.g., `feat: add STAT253 schedule builder`).
- PRs: clear description, linked issues, screenshots of dashboard changes, and sample generated outputs.
- Ensure `make validate`, `make lint`, `make format`, and `make test` pass; do not commit `build/` artifacts or secrets.

## Security & Configuration
- Never commit secrets; use environment variables. Start from `.env.example` → `.env` locally.
- Apply least privilege; prefer HTTPS endpoints. Sensitive data lives outside VCS.

## Agent-Specific Notes
- Prefer Make targets and existing utilities; avoid adding deps without checking `pyproject.toml`.
- Respect workspace boundaries; store generated files only under `build/`.
