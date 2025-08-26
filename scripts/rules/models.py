#!/usr/bin/env python3
"""Typed models for rules engine normalization.

These dataclasses capture raw facts, computed fields, and provenance
metadata for course data. They are intentionally generic to allow rule
families (dates, policy, compliance, dependencies) to annotate sources
and confidence levels.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class NormalizedField:
    """A normalized value with provenance and confidence."""

    value: Any
    original_value: Any
    sources: List[str] = field(default_factory=list)
    rules_applied: List[str] = field(default_factory=list)
    confidence: float = 1.0


@dataclass
class NormalizedCourse:
    """Normalized course snapshot produced by the rules engine.

    Attributes
    - course_id: canonical course identifier (e.g., "MATH221").
    - facts: immutable input facts loaded from JSON sources.
    - computed: derived structures produced by rules.
    - metadata: provenance, versions, timestamps, rule manifests.
    """

    course_id: str
    facts: Dict[str, Any] = field(default_factory=dict)
    computed: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_provenance(self, rule_name: str, rule_version: str) -> None:
        """Append rule application info to metadata."""
        applied = self.metadata.setdefault("rules_applied", [])
        applied.append({"name": rule_name, "version": rule_version})

