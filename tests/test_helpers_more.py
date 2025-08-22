#!/usr/bin/env python3
"""
Additional unit tests for dashboard.tools.helpers to increase coverage.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from dashboard.tools import helpers as H


def test_helpers_load_and_generate(tmp_path: Path):
    tpl = {"templates": [{"id": "x", "title": "Hello {course}", "category": "setup", "priority": "low", "days_before_start": 1}]}
    p = tmp_path / "tpl.json"
    p.write_text(json.dumps(tpl))
    templates = H.load_templates(p)
    assert len(templates) == 1

    course = {"code": "MATH221"}
    start = datetime(2025, 8, 25)
    t = H.generate_task_from_template(templates[0], course, start)
    assert t["title"] == "Hello MATH221" and t["due_date"] == "2025-08-24"

    all_tasks = H.generate_all_tasks([course], templates, start)
    assert len(all_tasks) == 1


def test_helpers_validation(tmp_path: Path):
    tasks = {
        "tasks": [
            {"id": "t1", "course": "X", "title": "A", "status": "todo", "priority": "low", "category": "setup", "due_date": "bad"},
            {"id": "t1", "course": "X", "title": "A2", "status": "todo", "priority": "low", "category": "setup", "depends_on": ["missing"]},
        ]
    }
    path = tmp_path / "tasks.json"
    path.write_text(json.dumps(tasks))

    summary = H.validate_all(path)
    assert summary["valid"] is False
    assert summary["error_count"] >= 2

