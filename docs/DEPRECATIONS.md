# Deprecations (Fall 2025 Merge Window)

The following compatibility shims exist to ease merging pre‑refactor feature branches into the V2 architecture. They will be removed after Fall 2025.

- `scripts/build_pipeline_impl.py`
  - Deprecated in favor of `scripts/build_pipeline.py` (enhanced staged pipeline).
- `scripts/rules/dates_full.py`
  - Deprecated in favor of `scripts/rules/dates.py` (unified DateRules).
- `scripts/schema/migrator.py`
  - Deprecated in favor of `scripts.migrations.add_stable_ids` and V2 schema helpers.
- `scripts/utils/schema/versions/v1_1_0.py` (module file)
  - Deprecated; import from the package path `scripts.utils.schema.versions.v1_1_0` instead.

These modules emit `DeprecationWarning` when imported. Plan removal once all downstream usages are updated.
