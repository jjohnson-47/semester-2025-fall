#!/usr/bin/env python3
"""Change detection (scaffold).

Computes per-course fingerprints and determines impacted build stages.
Real implementation will hash file contents and maintain history.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Change:
    kind: str
    path: str
    impact: list[str] | None = None


class ChangeDetector:
    """Detects changes and their impacts (placeholder)."""

    def detect_changes(self, course_id: str) -> list[Change]:
        _ = course_id
        return []

