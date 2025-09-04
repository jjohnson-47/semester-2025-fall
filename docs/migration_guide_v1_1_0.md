# Migration Guide: Schema v1.1.0 and Stable IDs

This guide describes how to adopt schema v1.1.0 for course schedules and add stable identifiers to schedule items while keeping current builds intact.

## Goals

- Add `_meta.schemaVersion` and standard headers to course data (v1.1.0)
- Introduce stable IDs for assignments/assessments to enable provenance and cross-referencing
- Preserve backward compatibility (string items remain accepted by v1.1.0 schema)

## Where schemas live

- `scripts/utils/schema/versions/v1_1_0/schedule.schema.json` (accepts string or `{id,title}`)
- `scripts/utils/schema/versions/v1_1_0/course.schema.json`

## Add stable IDs (non-destructive)

Generate a migrated copy with IDs for a course:

```bash
uv run python scripts/migrations/add_stable_ids.py \
  --course MATH221 \
  --in content/courses/MATH221/schedule.json \
  --out build/normalized/MATH221/schedule.v1_1_0.json \
  --vars variables/semester.json
```

Review the output and, when ready, replace the original schedule or keep both during transition.

## Validate against v1.1.0

You can validate a schedule document via the ValidationGateway in code/tests, or manually using `jsonschema` if preferred.

## Cutover strategy

1. Migrate schedules to include `id/title` pairs (or keep strings temporarily).  
2. Add `_meta` header to JSON data as you touch files.  
3. Keep `BUILD_MODE=legacy` while verifying parity; switch selectively to `v2` for templates/services that can consume projections.  
4. Update golden tests to anchor intentional deltas.

## Rollback

- Backups: keep original JSON unchanged until you have reviewed outputs.  
- Revert plan: you can always continue to use string entries; the v1.1.0 schedule schema supports both.

## Notes

- This guide is compatible with the existing Make targets; nothing in the legacy build path changes until the v2 projection is adopted in builders/templates.

