#!/usr/bin/env python3
"""Unified course service (scaffold).

Provides a single entry point for normalized course data and projections
for templates and task intelligence. This version defers real loading
and rule application to future iterations.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Dict

from scripts.rules.engine import CourseRulesEngine
from scripts.rules.models import NormalizedCourse


@dataclass
class CourseService:
    """Access normalized course data and projections (placeholder)."""

    course_id: str
    rules_engine: CourseRulesEngine | None = None

    def __post_init__(self) -> None:
        if self.rules_engine is None:
            self.rules_engine = CourseRulesEngine()
        self._normalized: NormalizedCourse | None = None
        self._cache_key: str | None = None

    @property
    def normalized(self) -> NormalizedCourse:
        key = self._compute_cache_key()
        if key != self._cache_key or self._normalized is None:
            # Real implementation will load facts then apply rules
            self._normalized = self.rules_engine.normalize_course(self.course_id)
            self._cache_key = key
        return self._normalized

    def get_template_context(self, template: str) -> Dict[str, Any]:
        """Project normalized data for templates (placeholder)."""
        _ = template
        return {"course": {"code": self.course_id}, "metadata": self.normalized.metadata}

    def _compute_cache_key(self) -> str:
        # Future: hash of file mtimes / fingerprints
        return hashlib.sha1(self.course_id.encode("utf-8")).hexdigest()

