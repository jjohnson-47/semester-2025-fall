#!/usr/bin/env python3
"""Projection adapter for BUILD_MODE=v2.

Unified adapter utilities for consuming CourseService v2 schedule projections.
V2 is now the default mode. Legacy mode is deprecated and will be removed.
"""

from __future__ import annotations

import os
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.services.course_service import CourseService


def is_v2_enabled() -> bool:
    """Check if V2 mode is enabled (now the default).
    
    V2 is the default mode. Legacy mode requires explicit BUILD_MODE=legacy.
    """
    build_mode = os.getenv("BUILD_MODE", "v2").lower()

    if build_mode == "legacy":
        warnings.warn(
            "Legacy mode is DEPRECATED and will be removed in the next release. "
            "Please use BUILD_MODE=v2 (now the default) for all operations.",
            DeprecationWarning,
            stacklevel=2
        )

    return build_mode == "v2"


def get_schedule_projection_weeks(course_code: str) -> list[dict[str, Any]]:
    """Return v2 projection weeks or an empty list if unavailable."""
    if not is_v2_enabled():
        return []
    svc = CourseService(content_dir=Path("content"))
    projection = svc.get_projection(course_code, "schedule")
    if projection and projection.data:
        weeks = projection.data.get("weeks", [])
        if isinstance(weeks, list):
            return weeks
    return []


@dataclass
class ProjectionAdapter:
    """Class-based adapter for tests expecting an adapter object.

    Provides a simple get_schedule_context API that returns a dict that may
    include a 'schedule_projection' key when BUILD_MODE=v2 is on.
    """

    content_dir: Path | str = Path("content")

    def get_schedule_context(self, course_id: str) -> dict[str, Any]:
        svc = CourseService(content_dir=Path(self.content_dir) if isinstance(self.content_dir, str) else self.content_dir)
        projection = svc.get_projection(course_id, "schedule")
        ctx = {}
        if projection and projection.data:
            ctx["schedule_projection"] = projection.data
        else:
            ctx["schedule_projection"] = {}
        return ctx
