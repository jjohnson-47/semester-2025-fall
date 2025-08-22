#!/usr/bin/env python3
"""
Smoke tests for type aliases to register module under coverage.
"""

from __future__ import annotations

from dashboard import type_aliases as T


def test_type_aliases_basic_usage():
    task: T.TaskDict = {"id": "X", "title": "T"}
    tasks: T.TaskList = [task]
    course: T.CourseDict = {"code": "MATH221"}
    resp: T.APIResponse = {"ok": True}
    stats: T.StatsDict = {"total": 1, "completion_rate": 0.0}
    ctx: T.TemplateContext = {"tasks": tasks, "course": course}

    assert isinstance(task, dict)
    assert isinstance(tasks, list)
    assert isinstance(resp, dict)
    assert isinstance(stats, dict)
    assert isinstance(ctx, dict)

