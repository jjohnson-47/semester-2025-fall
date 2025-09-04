# Orchestration Plan (V2 Integration)

This document supersedes the pre-refactor plan by aligning the staged build pipeline and date authority with the current V2 architecture.

## Goals

- Preserve the 6-stage pipeline (validate → normalize → project → generate → package → report) while integrating with V2 services/builders.
- Unify date rules under the rules engine with assignment-type preferences, holiday handling, and shift provenance.
- Provide compatibility shims so feature branches can merge cleanly without duplicating architecture.

## Implemented

- Enhanced pipeline in `scripts/build_pipeline.py` with per-stage CLI, verbose/dry-run, manifests, and reports.
- Compatibility wrapper `scripts/build_pipeline_impl.py` (re-exports upgraded pipeline class and CLI).
- Unified date rules (`scripts/rules/dates.py`) with preferences, holiday shifts, and provenance logging.
- Compatibility facade `scripts/rules/dates_full.py` for pre-refactor imports.
- Schema migrator compat at `scripts/schema/migrator.py` delegating to current migrations.
- v1.1.0 helper re-export at `scripts/utils/schema/versions/v1_1_0.py`.

## Orchestrated Workflow

- `make orchestrate -j3` runs validation, pipeline, and tests in parallel.
- Reports: `build/reports/build_summary.json`, `build/reports/build_report.md`.
- Manifests: per-course under `build/manifests/`, global under `build/package/manifest.json`.

## Merge Strategy

1. Land compatibility shims (done) to avoid breaking imports from feature branches.
2. Merge `feat/build-pipeline` and `feat/date-authority` into `main` (no behavioral change, just code history consolidation).
3. Retain wrappers for a deprecation window; point new work to consolidated modules.

## Next

- Optionally remove compatibility wrappers once downstream references are updated.

