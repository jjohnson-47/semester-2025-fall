# Site Builder Documentation

## Overview

The site builder creates a public-facing, security-hardened version of selected course materials for deployment to Cloudflare Pages under `site/`.

## Architecture Principles

- Separation: Public site (`site/`) is distinct from internal build outputs and dashboard (`build/`).
- Security: Default exclude all docs; explicit include only via flags.
- Reuse: Uses existing `SyllabusBuilder` and `ScheduleBuilder` for single source of truth.
- UV First: All Python execution through `uv run` (Make’s `$(PYTHON)` wrapper).

## Build Commands

### Basic build (empty structure)

```bash
make build-site ENV=preview
```

### Include Syllabus

```bash
$(PYTHON) scripts/site_build.py \
  --out site --env preview --term fall-2025 \
  --include-docs syllabus
```

### Include Schedule

```bash
$(PYTHON) scripts/site_build.py \
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

## Deployment Workflow

1. Local validation: `make build-site ENV=preview`
2. Manual trigger: Actions → “Cloudflare Pages Deploy” → Run workflow (choose environment)
3. Verify headers: `curl -I <url> | grep "frame-ancestors"`
4. Check manifest: `curl <url>/manifest.json | jq .`

## Notes

- The public site renders from data and templates; it does not copy HTML from `build/`.
- Course assets are copied minimally (`/assets/css/course.css`, `/assets/courses/<COURSE>.css`) if present.
- Schedules support will be added behind the same include/exclude controls once quality gates are met.
