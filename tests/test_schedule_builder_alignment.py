"""Tests for aligning course schedule with academic calendar."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("jsonschema")

from scripts.build_schedules import ScheduleBuilder


class FakeCalendar:
    def __init__(self) -> None:
        # Two instruction weeks + one finals week
        self._weeks = [
            {"start": "2025-08-25", "end": "2025-08-29", "holidays": [], "is_finals": False},
            {
                "start": "2025-09-01",
                "end": "2025-09-05",
                "holidays": ["Labor Day"],
                "is_finals": False,
            },
            {"start": "2025-12-08", "end": "2025-12-12", "holidays": [], "is_finals": True},
        ]

    def get_weeks(self) -> list[dict[str, Any]]:
        return self._weeks

    def get_semester_dates(self) -> dict[str, Any]:
        def d(s: str) -> datetime:
            return datetime.strptime(s, "%Y-%m-%d")

        return {
            "start": d("2025-08-25"),
            "end": d("2025-12-13"),
            "finals_start": d("2025-12-08"),
            "finals_end": d("2025-12-13"),
            "add_drop": d("2025-09-05"),
            "withdrawal": d("2025-10-31"),
        }


def test_build_schedule_aligns_weeks_and_due_dates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange: course schedule with 2 weeks and finals
    course_dir = tmp_path / "content" / "courses" / "TEST101"
    course_dir.mkdir(parents=True)
    schedule = {
        "weeks": [
            {"week": 1, "topic": "Intro", "assignments": ["HW1"], "assessments": ["Quiz 1"]},
            {"week": 2, "topic": "Derivatives", "assignments": ["HW2"], "assessments": []},
        ],
        "finals": {"topic": "Final Exam", "assessments": ["Final"]},
    }
    (course_dir / "schedule.json").write_text(json.dumps(schedule))

    # Builder with fake calendar
    out_dir = tmp_path / "build" / "schedules"
    builder = ScheduleBuilder(
        output_dir=str(out_dir), calendar=FakeCalendar(), content_root=tmp_path
    )

    # Act
    output_path = builder.build_schedule("TEST101")

    # Assert
    content = Path(output_path).read_text()
    # Week 1 dates aligned to Mon-Sun for 8/25-8/31
    assert "Aug 25 - Aug 31" in content
    # Homework due Friday by default (no weekends)
    assert "HW1 (due Fri 08/29)" in content
    # Holidays show in week 2
    assert "Labor Day" in content
    # Finals row present
    assert "Final Exam" in content and "Final" in content
