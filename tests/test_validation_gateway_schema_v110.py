#!/usr/bin/env python3
from __future__ import annotations

from scripts.services.validation import ValidationGateway


def test_schedule_schema_v110_accepts_string_items() -> None:
    vg = ValidationGateway()
    sched = {
        "weeks": [
            {
                "week": 1,
                "topic": "T",
                "readings": ["1.1"],
                "assignments": ["HW 1"],
                "assessments": ["Exam #1"],
                "notes": "",
            }
        ]
    }
    res = vg.validate_schedule_v1_1_0(sched)
    assert res.ok, res.messages


def test_schedule_schema_v110_accepts_object_items() -> None:
    vg = ValidationGateway()
    sched = {
        "weeks": [
            {
                "week": 1,
                "topic": "T",
                "readings": ["1.1"],
                "assignments": [{"id": "2025FA-C-HW-01", "title": "HW 1"}],
                "assessments": [{"id": "2025FA-C-EXAM-01", "title": "Exam #1"}],
                "notes": "",
            }
        ],
        "finals": {
            "topic": "Final",
            "assessments": [{"id": "2025FA-C-FIN-01", "title": "Final Exam"}],
            "notes": "",
        },
    }
    res = vg.validate_schedule_v1_1_0(sched)
    assert res.ok, res.messages
