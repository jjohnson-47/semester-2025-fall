# ADR 0003: Unified Build Pipeline

- Status: Proposed
- Date: 2025-08-25

## Context
Current build relies on discrete scripts; we need a deterministic, staged pipeline with change detection.

## Decision
- Introduce `BuildPipeline` with stages: validate → normalize → project → generate → package → report.
- Write change detection (fingerprints) to skip unchanged courses.

## Consequences
- Improves reproducibility and observability (per-course reports, manifests).
- Adds orchestration code and CI hooks.

## Implementation Notes
- Keep Makefile targets; enable a `BUILD_MODE=v2` cutover flag during transition.

