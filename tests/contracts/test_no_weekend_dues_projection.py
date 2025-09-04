#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from scripts.services.course_service import CourseService


def _iter_courses() -> list[str]:
    root = Path("content/courses")
    return sorted(p.name for p in root.iterdir() if p.is_dir())


def test_projection_no_weekend_dues(monkeypatch) -> None:
    monkeypatch.setenv("BUILD_MODE", "v2")
    for course in _iter_courses():
        svc = CourseService(course)
        ctx = svc.get_template_context("schedule")
        proj = ctx.get("schedule_projection", {})
        for wk in proj.get("weeks", []):
            for label in wk.get("assignments", []) + wk.get("assessments", []):
                assert "(due Sat" not in label
                assert "(due Sun" not in label

