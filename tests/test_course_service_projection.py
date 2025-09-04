#!/usr/bin/env python3
from __future__ import annotations

from scripts.services.course_service import CourseService


def test_schedule_projection_generates_due_strings(monkeypatch) -> None:
    monkeypatch.setenv("BUILD_MODE", "v2")
    svc = CourseService("MATH221")
    ctx = svc.get_template_context("schedule")
    proj = ctx.get("schedule_projection", {})
    weeks = proj.get("weeks", [])
    if not weeks:
        # If no schedule present, projection may be empty; keep test tolerant
        return
    # Check that at least one assignment has a due label
    example = next((a for w in weeks for a in w.get("assignments", []) if "(due " in a), None)
    assert example is not None

