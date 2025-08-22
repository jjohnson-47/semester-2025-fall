#!/usr/bin/env python3
"""
Unit tests for dashboard.tools.validate.TaskValidator (class-based path).
"""

from __future__ import annotations

import json
from pathlib import Path

from dashboard.tools.validate import TaskValidator


def test_taskvalidator_validate_full(tmp_path: Path):
    tasks = {
        "tasks": [
            # Missing required field 'title' -> error in required fields check
            {"id": "A", "course": "X", "status": "todo"},
            # Invalid due date string under 'due' field -> error in _validate_dates
            {"id": "B", "course": "X", "title": "B", "status": "todo", "due": "bad-date"},
            # Invalid status -> error in _validate_statuses
            {"id": "C", "course": "X", "title": "C", "status": "unknown"},
            # Blocked with no blocked_by -> warning in _validate_statuses
            {"id": "D", "course": "X", "title": "D", "status": "blocked"},
            # Duplicates -> error in _check_duplicates
            {"id": "A", "course": "X", "title": "Dupe", "status": "todo"},
            # For circular dependency detection: E -> F and F -> E
            {"id": "E", "course": "X", "title": "E", "status": "todo", "blocked_by": ["F"]},
            {"id": "F", "course": "X", "title": "F", "status": "todo", "blocked_by": ["E"]},
            # Missing dependency -> error in _validate_dependencies
            {"id": "G", "course": "X", "title": "G", "status": "todo", "blocked_by": ["NOPE"]},
        ]
    }
    p = tmp_path / "tasks.json"
    p.write_text(json.dumps(tasks))

    v = TaskValidator(str(p))
    ok = v.validate()
    assert ok is False
    # Expect multiple errors to be recorded
    assert len(v.errors) >= 4
    # And at least one warning about blocked with no dependencies
    assert any("blocked" in w for w in v.warnings)


def test_taskvalidator_missing_file(tmp_path: Path):
    p = tmp_path / "missing.json"
    v = TaskValidator(str(p))
    assert v.validate() is False

