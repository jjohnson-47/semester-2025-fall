## Summary

- What changed and why:
- Related issues:

## Quality Gates

- [ ] `make validate` passes
- [ ] `uv run ruff format` applied and `uv run ruff check .` passes
- [ ] `uv run mypy dashboard/ scripts/ --strict` passes
- [ ] `uv run pytest -q` passes with ≥85% coverage on changed modules
- [ ] No secrets added; `.env` patterns respected

## Contracts & Goldens

- [ ] Contract tests added/updated (if applicable)
- [ ] Golden tests updated only with justification and ADR link (if applicable)

## Docs

- [ ] Updated docs/ and ADRs as needed

## Deployment Notes

- Feature flags or cutover steps:
- Backward compatibility considerations:

