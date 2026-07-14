# Site Builder Documentation

> **Current archive tool.** The builder remains supported for reproducing the
> retained Fall 2025 public archive locally. External publication is retired as
> of 2026-07-14; a successful build does not deploy anything. See
> [`adr/0005-retained-public-archive.md`](adr/0005-retained-public-archive.md).

## Overview

The site builder creates a public-facing, security-hardened version of selected course materials under `site/`. The output is retained archive material and can be inspected locally without Cloudflare credentials.

## Architecture Principles

- Separation: Public site (`site/`) is distinct from internal build outputs and dashboard (`build/`).
- Security: Default exclude all docs; explicit include only via flags.
- Reuse: Uses existing `SyllabusBuilder` and `ScheduleBuilder` for single source of truth.
- UV First: All Python execution through `uv run` (Make’s `$(PYTHON)` wrapper).

## Build Commands

### Basic build (empty structure)

```bash
BUILD_MODE=v2 make build-site ENV=preview
```

### Include Syllabus

```bash
uv run python scripts/site_build.py \
  --out site --env preview --term fall-2025 \
  --include-docs syllabus
```

### Include Schedule

```bash
uv run python scripts/site_build.py \
  --out site --env preview --term fall-2025 \
  --include-docs schedule
```

## Flags

- `--include-docs`: Only include these doc types (e.g., `syllabus`, `schedule`). Overrides excludes.
- `--exclude-docs`: Exclude these doc types. Defaults to `syllabus schedule` for safety.
- `--courses`: Limit to specific courses (defaults to MATH221, MATH251, STAT253).
- `--term`: Academic term label used in URLs (default `fall-2025`).

## Security Boundaries

- CSP: `_headers` enforces `frame-ancestors 'none'` by default.
- No dashboard URLs or internal APIs are referenced in public templates.
- No task system or admin features are included.

## Archive Verification Workflow

1. Validate sources: `BUILD_MODE=v2 make validate`.
2. Rebuild locally: `BUILD_MODE=v2 make build-site ENV=preview`.
3. Confirm `site/manifest.json` and `site/_headers` exist.
4. Optionally serve `site/` locally with `BUILD_MODE=v2 make serve-site`.

These steps do not mutate or redeploy the retained Cloudflare Pages site.
Automatic and manually triggered publication are retired. Any reactivation
requires a new owner decision and the gate in ADR 0005.

## Notes

- The public site renders from data and templates; it does not copy HTML from `build/`.
- Course assets are copied minimally (`/assets/css/course.css`, `/assets/courses/<COURSE>.css`) if present.
- Syllabi and schedules remain subject to the same explicit include/exclude controls.
