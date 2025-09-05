# QA Fix Plan — Format, Lint, Mypy (Red → Green)

Generated: 2025-09-04

This plan turns the three failing checks (Format, Lint, Mypy) green and locks in the behavior with guardrails already present in this repo.

- Status basis: docs/STATUS_REPORT.md (live, code-based)
- Diagnostics: docs/DIAGNOSTICS_DIRECTIVE.md (exact command block)

## Current Status (Evidence)

- Format: FAIL — ruff format wants changes in `dashboard/startup.py`.
- Lint: FAIL — RUF006 (must store `asyncio.create_task` return).
  - Call sites found in repo:
    - `claude_init.py:223` — `_monitor_task = asyncio.create_task(system.start_monitoring())` (already stored; confirm lifecycle mgmt)
    - `dashboard/advanced_orchestrator.py:440` — `asyncio.create_task(workflow.execute())` (fire-and-forget; needs tracking)
- Mypy: FAIL — `scripts/utils/style_system.py:106 [dict-item]` — `Dict entry 2 has incompatible type "str": "bool"; expected "str": "str"`.
  - Context culprit appears to be `has_embedded_styles: True` in a dict that mypy infers as `dict[str, str]` at that site.

## Do This Next (Copy-Paste)

1) Create branch + capture diagnostics

```bash
git checkout -b chore/qa-fmt-lint-mypy
# Paste the full output into the PR under “Evidence”
bash -lc "$(cat docs/DIAGNOSTICS_DIRECTIVE.md | sed -n 's/^```bash$//; t; /^[`][`][`]$/q; p')"
```

2) Fixes in fastest path order

A. Format (mechanical)

```bash
make fmt
# commit only format diffs
```

B. Lint (RUF006) — manage background tasks explicitly

- For `dashboard/advanced_orchestrator.py:440`:
  - Prefer structured concurrency if you can await completion at the call site:

    ```py
    async with asyncio.TaskGroup() as tg:
      tg.create_task(workflow.execute(), name="workflow.execute")
    ```

  - If the task must outlive the scope, track it in a module-level set:

    ```py
    _bg_tasks: set[asyncio.Task[None]] = set()

    def _track(t: asyncio.Task[None]) -> None:
        _bg_tasks.add(t)
        t.add_done_callback(_bg_tasks.discard)

    t = asyncio.create_task(workflow.execute(), name="workflow.execute")
    _track(t)
    ```

- For `claude_init.py:223` (already stored):
  - Ensure lifecycle: on shutdown, `cancel()` tasks and `await asyncio.gather(*_bg_tasks, return_exceptions=True)`.

Re-run:

```bash
ruff check --select RUF006
```

C. Mypy — correct style mapping type in `scripts/utils/style_system.py`

Choose one based on intended contract:

- If consumers accept non-strings (recommended; current return is `dict[str, Any]`):
  - Make the local object type explicit to `dict[str, str | bool]` or introduce a `TypedDict` for the style context fragment:

    ```py
    from typing import TypedDict

    class _StyleCtx(TypedDict, total=False):
        base_css_content: str
        course_css_content: str
        base_css_path: str
        course_css_path: str
        has_embedded_styles: bool
        font_imports: str

    context: _StyleCtx = {
        "style_mode": "embedded" if self.config.should_embed() else "linked",
        "font_imports": self._get_font_imports(),
    }
    ```

- If a pure `dict[str, str]` is required elsewhere:
  - Coerce booleans to strings at construction time: `"true"/"false"` and widen annotations accordingly.

Re-run:

```bash
make typecheck
```

3) Commit in small slices

- `style: format code (ruff)`
- `lint: manage asyncio background tasks (RUF006)`
- `types: correct style context typing (mypy [dict-item])`

4) Verify locally and push

```bash
make lint
make typecheck
make test
make cov-xml && make ratchet
```

## Acceptance Criteria (Green)

- `ruff format --check` → PASS
- `ruff check` (incl. RUF006) → PASS
- `mypy .` (focused paths) → PASS
- Coverage ratchet → PASS
- Background task lifecycle (if used): tasks are stored, named, and cancelled on shutdown.

## Notes & Guardrails (Locked In)

- Suppress policy enforced by CI: only `dashboard/startup.py` may use `contextlib.suppress`.
- Ratchet baseline auto-advances on improvements ≥0.5pp, prevents regressions >0.5pp.
- Test DB watchdog (SQLite progress handler) aborts overlong statements when `TEST_DB_STATEMENT_TIMEOUT_MS` is set (CI=2000ms).

## Appendix — Exact Call Sites

- `claude_init.py:223`
- `dashboard/advanced_orchestrator.py:440`

## Appendix — Affected Files

- `dashboard/startup.py` (format)
- `dashboard/advanced_orchestrator.py` (RUF006)
- `claude_init.py` (validate lifecycle)
- `scripts/utils/style_system.py` (mypy dict-item)

