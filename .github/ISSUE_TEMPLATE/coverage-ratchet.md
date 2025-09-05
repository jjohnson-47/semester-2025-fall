---
name: Add coverage ratchet
about: Implement and wire coverage ratchet to prevent regressions
title: Add coverage ratchet
labels: ci, testing
assignees: ''
---

Implement `scripts/ci/coverage_ratchet.py`, add `make ratchet`, run after tests, store `.ratchet/base_coverage.txt` in repo. Acceptable drop ≤0.5pp; auto-advance baseline on ≥0.5pp improvement.

