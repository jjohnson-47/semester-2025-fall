#!/usr/bin/env python3
"""
Unit tests for SmartPrioritizer and TaskGraph in reprioritize engine.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from dashboard.tools.reprioritize import SmartPrioritizer, TaskGraph


def _sample_tasks():
    today = datetime.now().date()
    return [
        {
            "id": "A-SETUP",
            "course": "MATH221",
            "title": "Setup",
            "status": "done",
            "category": "setup",
            "weight": 2,
            "due_date": (today - timedelta(days=2)).isoformat(),
        },
        {
            "id": "B-CONTENT",
            "course": "MATH221",
            "title": "Write content",
            "status": "todo",
            "category": "content",
            "depends_on": ["A-SETUP"],
            "updated_at": (datetime.now() - timedelta(days=30)).isoformat(),
            "weight": 3,
        },
        {
            "id": "C-QUIZ",
            "course": "MATH251",
            "title": "Build quiz",
            "status": "blocked",
            "category": "assessment",
            "depends_on": ["B-CONTENT"],
            "weight": 1,
        },
    ]


def _contracts():
    return {
        "coefficients": {
            "alpha_due": 1.0,
            "beta_critical": 2.0,
            "gamma_impact": 1.5,
            "delta_proximity": 1.0,
            "epsilon_head": 5.0,
            "zeta_phase": 0.5,
        },
        "anchors": [{"id_suffix": "QUIZ"}],
        "now_queue": {"max_items": 5, "per_course_limit": 2, "ensure_each_course": True},
        "pins": {"by_id": ["B-CONTENT"], "pin_boost": 50.0},
        "staleness": {
            "enabled": True,
            "days_until_stale": 7,
            "stale_penalty": -1.0,
            "max_penalty": -10.0,
        },
        "phases": {
            "build": {"start_days": -3, "end_days": 10, "category_boosts": {"content": 2.0}}
        },
        "critical_path": {"method": "sum", "distance_decay": 0.9},
    }


def test_taskgraph_methods():
    tasks = _sample_tasks()
    g = TaskGraph(tasks)
    # Anchors by suffix
    anchors = g.find_anchors([{"id_suffix": "QUIZ"}])
    assert "C-QUIZ" in anchors
    # Blocked descendants of A include C (through B)
    descendants = g.get_blocked_descendants("A-SETUP")
    assert "C-QUIZ" in descendants
    # Chain head: B is todo and all deps (A) are done
    assert g.is_chain_head("B-CONTENT") is True


def test_smart_prioritizer_scoring_and_queue():
    tasks = _sample_tasks()
    p = SmartPrioritizer(
        tasks,
        _contracts(),
        semester_first_day=(datetime.now() - timedelta(days=1)).date().isoformat(),
    )
    # Score a task
    scored = p.calculate_smart_score(dict(tasks[1]))
    assert "smart_score" in scored and isinstance(scored["smart_score"], float)
    assert "score_breakdown" in scored

    # Build now queue
    queue = p.build_now_queue()
    assert len(queue) >= 1
    # Ensure chain head flag present
    assert all("is_chain_head" in t for t in queue)

    # Run full process path to exercise logging and aggregation
    tasks_after, now_queue = p.process()
    assert isinstance(tasks_after, list) and isinstance(now_queue, list)
    assert all("smart_score" in t for t in tasks_after if t.get("status") != "done")
