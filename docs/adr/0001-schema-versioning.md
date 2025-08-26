# ADR 0001: Schema Versioning and Stable IDs

- Status: Proposed
- Date: 2025-08-25

## Context
Course JSON lacks stable identifiers and explicit schema versions, complicating migrations, provenance, and cross-system references.

## Decision
- Introduce `_meta.schemaVersion` and `_meta` header in all JSON data files.
- Add stable IDs for schedule/assessment artifacts per refactor plan.
- Maintain versioned schemas under `scripts/utils/schema/versions/` and a `SchemaMigrator` to evolve data.

## Consequences
- Enables safe, incremental migrations and compatibility windows.
- Slightly increases data verbosity; tooling must enforce headers.

## Implementation Notes
- Write migrator and tests; dry-run before committing transformed fixtures.

