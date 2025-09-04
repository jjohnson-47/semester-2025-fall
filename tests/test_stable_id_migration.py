#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from scripts.migrations.add_stable_ids import (
    classify_item,
    generate_stable_id,
    infer_term_label,
    migrate_schedule,
)


def test_term_inference() -> None:
    tf = Path("variables/semester.json")
    assert infer_term_label(tf).startswith("2025")


def test_classify_and_generate_ids() -> None:
    assert classify_item("Blackboard Discussion: Week 1", False) == "DISC"
    assert classify_item("MyOpenMath: HW 1", False) == "HW"
    assert classify_item("Exam #1", True) == "EXAM"
    assert classify_item("Quiz #1", True) == "QUIZ"
    sid = generate_stable_id("2025FA", "MATH221", "HW", 1)
    assert sid == "2025FA-MATH221-HW-01"


def test_migrate_schedule_structure(tmp_path: Path) -> None:
    sample = {
        "weeks": [
            {
                "topic": "T",
                "assignments": ["HW 1", "Blackboard Discussion: Intro"],
                "assessments": ["Exam #1"],
            }
        ],
        "finals": {"topic": "Final", "assessments": ["Final Exam"]},
    }
    migrated = migrate_schedule("MATH221", sample, "2025FA")
    wk = migrated["weeks"][0]
    assert isinstance(wk["assignments"][0], dict) and "id" in wk["assignments"][0]
    assert isinstance(wk["assessments"][0], dict) and "id" in wk["assessments"][0]
    assert migrated["finals"]["assessments"][0]["id"].startswith("2025FA-MATH221-FIN-")

