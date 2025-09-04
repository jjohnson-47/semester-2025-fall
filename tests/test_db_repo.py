#!/usr/bin/env python3
"""
Unit tests for dashboard.db.repo.Database.
Covers schema init, CRUD, deps, scores, and now_queue operations.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from dashboard.db import Database, DatabaseConfig


@pytest.fixture()
def temp_db(tmp_path: Path) -> Database:
  dbp = tmp_path / "tasks.db"
  db = Database(DatabaseConfig(dbp))
  db.initialize()
  # Ensure clean
  with db.connect() as conn:
    conn.execute("delete from now_queue")
    conn.execute("delete from scores")
    conn.execute("delete from deps")
    conn.execute("delete from tasks")
  return db


def test_crud_and_list_filters(temp_db: Database, tmp_path: Path) -> None:
  db = temp_db
  # Create a few tasks
  t1 = {
    "id": "T-1",
    "course": "MATH221",
    "title": "A",
    "status": "todo",
    "category": "setup",
    "due_at": "2025-08-20",
    "est_minutes": 30,
    "notes": "alpha",
  }
  t2 = {
    "id": "T-2",
    "course": "MATH251",
    "title": "B",
    "status": "doing",
    "category": "content",
    "est_minutes": 45,
    "notes": "beta",
  }
  for t in (t1, t2):
    db.create_task(t)

  # List all
  all_tasks = db.list_tasks()
  assert len(all_tasks) == 2

  # Filter by status
  doing = db.list_tasks(status="doing")
  assert len(doing) == 1 and doing[0]["id"] == "T-2"

  # Filter by course
  m221 = db.list_tasks(course="MATH221")
  assert len(m221) == 1 and m221[0]["id"] == "T-1"

  # Update fields
  assert db.update_task_field("T-1", "status", "review")
  assert db.update_task_fields("T-2", {"title": "B2", "weight": 2.0, "notes": "b2"})
  after = {t["id"]: t for t in db.list_tasks()}
  assert after["T-1"]["status"] == "review"
  assert after["T-2"]["title"] == "B2" and int(after["T-2"]["weight"]) == 2

  # Deps
  db.add_deps("T-2", ["T-1"])  # T-2 depends on T-1
  with db.connect() as conn:
    rows = conn.execute("select * from deps").fetchall()
  assert len(rows) == 1 and rows[0]["task_id"] == "T-2" and rows[0]["blocks_id"] == "T-1"

  # Scores upsert/get
  db.upsert_score("T-1", 12.34, {"alpha": 1.0})
  sc = db.get_score("T-1")
  assert sc is not None and abs(float(sc["score"]) - 12.34) < 1e-6

  # Now queue operations
  db.set_now_queue(["T-2", "T-1"])
  assert db.get_now_queue() == ["T-2", "T-1"]
  db.remove_from_now_queue("T-2")
  assert db.get_now_queue() == ["T-1"]

  # Export/import JSON roundtrip
  snap = tmp_path / "tasks.json"
  db.export_snapshot_to_json(snap)
  payload = json.loads(snap.read_text())
  assert "tasks" in payload and len(payload["tasks"]) == 2

  # Delete one
  assert db.delete_task("T-2")
  assert all(t["id"] != "T-2" for t in db.list_tasks())

