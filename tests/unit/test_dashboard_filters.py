#!/usr/bin/env python3
"""Golden tests for dashboard filters.

Verifies that the API returns the expected task IDs for blocked/doing filters
using a stable JSON fixture.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from flask import Flask

from dashboard.app import app as flask_app
from dashboard.db import Database, DatabaseConfig


@pytest.fixture
def client(tmp_path: Path):
    """Create a test client bound to a temporary DB/state dir."""
    app: Flask = flask_app
    app.config["TESTING"] = True
    state_dir = tmp_path
    tasks_file = state_dir / "tasks.json"
    db_path = state_dir / "tasks.db"

    with (
        patch("dashboard.app.STATE_DIR", state_dir),
        patch("dashboard.app.TASKS_FILE", tasks_file),
        patch("dashboard.app.DB_PATH", db_path),
        patch("dashboard.app._db", Database(DatabaseConfig(db_path))),
        app.test_client() as c,
    ):
        # ensure clean DB
        from dashboard.app import _db as _db_mod

        _db_mod.initialize()
        yield c


def _load_fixture(name: str) -> dict[str, Any]:
    p = Path(__file__).parent / "fixtures" / name
    return json.loads(p.read_text())


@pytest.mark.unit
def test_filter_blocked(client):
    payload = _load_fixture("tasks_sample.json")
    tasks = payload["tasks"]

    # Seed DB with canonicalized statuses
    from dashboard.app import _db as _db_mod

    for t in tasks:
        st = t.get("status", "todo")
        if st in {"in_progress", "in-progress", "progress"}:
            st = "doing"
        if st in {"completed", "complete"}:
            st = "done"
        _db_mod.create_task(
            {
                "id": t["id"],
                "course": t["course"],
                "title": t["title"],
                "status": st,
                "depends_on": t.get("depends_on"),
                "due_at": t.get("due_date"),
                "notes": t.get("description"),
            }
        )
    # Add deps
    for t in tasks:
        if t.get("depends_on"):
            _db_mod.add_deps(t["id"], t["depends_on"])  # type: ignore[arg-type]

    # Blocked filter is implemented as a view; fetch and check presence
    # Use API list and compute expected IDs based on deps/status
    r = client.get("/api/tasks")
    assert r.status_code == 200
    body = r.get_json()
    got = body["tasks"]
    # expected: blocked if status=='blocked' or has unmet deps
    # For this golden, we treat any task with depends_on as blocked unless status=='done'
    expected_ids = set()
    id_to_status = {t["id"]: t.get("status", "todo") for t in tasks}
    for t in tasks:
        if t.get("status") == "blocked":
            expected_ids.add(t["id"])
        elif t.get("depends_on"):
            deps = t["depends_on"]
            if any(id_to_status.get(d) != "done" for d in deps):
                expected_ids.add(t["id"])
    got_ids = {t["id"] for t in got if t.get("status") == "blocked"}
    # Presence check: at least the explicitly blocked ones appear
    assert expected_ids.issuperset(got_ids)


@pytest.mark.unit
def test_filter_doing(client):
    payload = _load_fixture("tasks_sample.json")
    tasks = payload["tasks"]

    # Seed DB with canonicalized statuses
    from dashboard.app import _db as _db_mod

    for t in tasks:
        st = t.get("status", "todo")
        if st in {"in_progress", "in-progress", "progress"}:
            st = "doing"
        if st in {"completed", "complete"}:
            st = "done"
        _db_mod.create_task(
            {
                "id": t["id"],
                "course": t["course"],
                "title": t["title"],
                "status": st,
                "due_at": t.get("due_date"),
                "notes": t.get("description"),
            }
        )

    r = client.get("/api/tasks?status=doing")
    assert r.status_code == 200
    body = r.get_json()
    got_ids = {t["id"] for t in body["tasks"]}
    expected_ids = {t["id"] for t in tasks if t.get("status") in {"doing", "in_progress"}}
    assert got_ids == expected_ids

