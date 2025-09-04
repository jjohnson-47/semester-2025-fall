#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from scripts.services.course_service import CourseService


def test_math221_projection_week1_matches_golden() -> None:
    svc = CourseService("MATH221")
    proj = svc.project_schedule_with_due_dates()
    weeks = proj.get("weeks", [])
    assert weeks, "Projection should have weeks"
    w1 = weeks[0]
    golden = json.loads(
        Path("tests/golden/MATH221.schedule.projection.v2.golden.json").read_text(encoding="utf-8")
    )
    g1 = golden["weeks"][0]
    # Topic equality
    assert w1.get("topic") == g1.get("topic")
    # At least the two expected labels are present in assignments
    def _base(s: str) -> str:
        return s.split(" (due")[0] if isinstance(s, str) else s

    got = set(_base(s) for s in w1.get("assignments", []))
    exp = set(_base(s) for s in g1.get("assignments", []))
    assert exp.issubset(got)
