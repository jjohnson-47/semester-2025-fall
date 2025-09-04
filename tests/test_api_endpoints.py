#!/usr/bin/env python3
"""
Unit tests for REST API endpoints (tasks, stats, export, courses).
Exercises blueprint routes to increase coverage.
"""

from __future__ import annotations

import json

import pytest

from dashboard import create_app
from dashboard.config import Config
from dashboard.db import Database, DatabaseConfig


@pytest.fixture
def app():
    app = create_app("testing")
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def _seed_tasks() -> list[dict]:
    return [
        {
            "id": "T-001",
            "course": "MATH221",
            "title": "A",
            "status": "todo",
            "priority": "medium",
            "category": "setup",
            "due_date": "2025-08-20",
        },
        {
            "id": "T-002",
            "course": "MATH251",
            "title": "B",
            "status": "in_progress",
            "priority": "high",
            "category": "technical",
        },
        {
            "id": "T-003",
            "course": "MATH221",
            "title": "C",
            "status": "completed",
            "priority": "low",
            "category": "content",
            "due_date": "2025-08-22",
        },
    ]


def test_tasks_crud_and_filters(app, client):
    # Seed via DB (API_FORCE_DB enabled in testing)
    with app.app_context():
        db = Database(DatabaseConfig(Config.STATE_DIR / "tasks.db"))
        db.initialize()
        # Clear any existing
        with db.connect() as conn:
            conn.execute("delete from deps")
            conn.execute("delete from now_queue")
            conn.execute("delete from tasks")
        for t in _seed_tasks():
            status = t["status"]
            if status == "in_progress":
                status = "doing"
            elif status == "completed":
                status = "done"
            db.create_task(
                {
                    "id": t["id"],
                    "course": t["course"],
                    "title": t["title"],
                    "status": status,
                    "category": t.get("category"),
                    "due_at": t.get("due_date"),
                    "notes": t.get("description"),
                }
            )

    # GET list and filter
    resp = client.get("/api/tasks?course=MATH221")
    assert resp.status_code == 200
    payload = resp.get_json()
    assert len(payload["tasks"]) == 2

    # GET one
    resp = client.get("/api/tasks/T-002")
    assert resp.status_code == 200
    assert resp.get_json()["id"] == "T-002"

    # GET missing
    assert client.get("/api/tasks/MISSING").status_code == 404

    # POST invalid content-type
    resp = client.post(
        "/api/tasks", data=json.dumps({"x": 1}), headers={"Content-Type": "text/plain"}
    )
    assert resp.status_code == 400

    # POST missing fields
    resp = client.post("/api/tasks", json={"course": "MATH221"})
    assert resp.status_code == 400

    # POST ok
    new_task = {
        "course": "STAT253",
        "title": "New",
        "status": "todo",
        "priority": "medium",
        "category": "setup",
    }
    resp = client.post("/api/tasks", json=new_task)
    assert resp.status_code == 201
    created = resp.get_json()
    assert created["id"]

    # PUT update
    resp = client.put(f"/api/tasks/{created['id']}", json={"status": "in_progress"})
    assert resp.status_code == 200
    assert resp.get_json()["task"]["status"] in {"in_progress", "doing"}

    # PATCH status invalid body
    resp = client.patch(f"/api/tasks/{created['id']}/status", json={})
    assert resp.status_code == 400

    # PATCH invalid status
    resp = client.patch(f"/api/tasks/{created['id']}/status", json={"status": "INVALID"})
    assert resp.status_code == 400

    # PATCH valid
    resp = client.patch(f"/api/tasks/{created['id']}/status", json={"status": "todo"})
    assert resp.status_code == 200

    # DELETE missing
    assert client.delete("/api/tasks/DOES-NOT-EXIST").status_code == 404

    # DELETE ok
    assert client.delete(f"/api/tasks/{created['id']}").status_code == 200


def test_stats_endpoints(app, client):
    with app.app_context():
        db = Database(DatabaseConfig(Config.STATE_DIR / "tasks.db"))
        db.initialize()
        with db.connect() as conn:
            conn.execute("delete from deps")
            conn.execute("delete from now_queue")
            conn.execute("delete from tasks")
        for t in _seed_tasks():
            status = t["status"]
            if status == "in_progress":
                status = "doing"
            elif status == "completed":
                status = "done"
            db.create_task(
                {
                    "id": t["id"],
                    "course": t["course"],
                    "title": t["title"],
                    "status": status,
                    "category": t.get("category"),
                    "due_at": t.get("due_date"),
                    "notes": t.get("description"),
                }
            )

    # Overall stats
    resp = client.get("/api/stats")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["total"] == 3
    assert data["completed"] == 1
    assert data["todo"] == 1

    # Course stats
    resp = client.get("/api/stats/courses/MATH221")
    assert resp.status_code == 200
    course_data = resp.get_json()
    assert course_data["course"] == "MATH221"
    assert course_data["total"] >= 1

    # Unknown course
    assert client.get("/api/stats/courses/NOPE").status_code == 404


def test_export_endpoints(app, client):
    with app.app_context():
        db = Database(DatabaseConfig(Config.STATE_DIR / "tasks.db"))
        db.initialize()
        with db.connect() as conn:
            conn.execute("delete from deps")
            conn.execute("delete from now_queue")
            conn.execute("delete from tasks")
        for t in _seed_tasks():
            status = t["status"]
            if status == "in_progress":
                status = "doing"
            elif status == "completed":
                status = "done"
            db.create_task(
                {
                    "id": t["id"],
                    "course": t["course"],
                    "title": t["title"],
                    "status": status,
                    "category": t.get("category"),
                    "due_at": t.get("due_date"),
                    "notes": t.get("description"),
                }
            )

    # JSON export
    resp = client.get("/api/export/json?course=MATH221")
    assert resp.status_code == 200
    assert resp.mimetype == "application/json"
    payload = json.loads(resp.data.decode("utf-8"))
    assert payload["count"] == 2

    # CSV export
    resp = client.get("/api/export/csv")
    assert resp.status_code == 200
    assert resp.mimetype == "text/csv"
    assert "Content-Disposition" in resp.headers

    # ICS export contains calendar and at least one VEVENT for due_date tasks
    resp = client.get("/api/export/ics")
    assert resp.status_code == 200
    assert resp.mimetype == "text/calendar"
    text = resp.data.decode("utf-8")
    assert "BEGIN:VCALENDAR" in text and "END:VCALENDAR" in text
    assert "BEGIN:VEVENT" in text


def test_courses_endpoints(app, client):  # noqa: ARG001
    # List
    resp = client.get("/api/courses")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["total"] >= 1
    assert any(c["code"] == "MATH221" for c in data["courses"])

    # Detail ok
    assert client.get("/api/courses/MATH221").status_code == 200
    # Not found
    assert client.get("/api/courses/UNKNOWN").status_code == 404
