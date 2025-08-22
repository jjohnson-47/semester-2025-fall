#!/usr/bin/env python3
"""
Integration-style unit test for YAML TaskGenerator path in generate_tasks.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from dashboard.tools.generate_tasks import TaskGenerator


@pytest.mark.unit
def test_taskgenerator_yaml_end_to_end(tmp_path: Path):
    # Courses file with important dates
    courses_data = {
        "semester": "2025-fall",
        "important_dates": {"first_day": "2025-08-25", "last_day": "2025-12-13"},
        "courses": [
            {"code": "MATH221", "name": "Calc I"},
            {"code": "MATH251", "name": "Calc II"},
        ],
    }
    courses_file = tmp_path / "courses.json"
    courses_file.write_text(json.dumps(courses_data))

    # YAML template with applies_to ALL and defaults
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    yaml_content = """
defaults:
  category: setup
  weight: 2
applies_to: [ALL]
tasks:
  - id: "{{course.code}}-INTRO"
    title: "Prepare intro for {{course.code}}"
    due_offset: {days: 7, from: "semester.first_day"}
  - key: "BB-SETUP"
    title: "Setup BB for {{course.code}}"
    blocked_by: "{{course.code}}-INTRO"
    due_offset: {days: 10, from: "semester.first_day"}
"""
    (templates_dir / "setup.yaml").write_text(yaml_content)

    gen = TaskGenerator(str(courses_file), str(templates_dir))
    result = gen.generate()

    tasks = result["tasks"]
    # Should generate 2 courses × 2 tasks each
    assert len(tasks) == 4

    # Each should have due_date and depends_on mapped for second task
    ids = {t["id"] for t in tasks}
    assert "MATH221-INTRO" in ids and "MATH251-BB-SETUP" in ids
    by_id = {t["id"]: t for t in tasks}
    assert by_id["MATH221-BB-SETUP"]["depends_on"] == ["MATH221-INTRO"]
    assert any("due_date" in t for t in tasks)
