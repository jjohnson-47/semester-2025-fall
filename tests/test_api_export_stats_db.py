#!/usr/bin/env python3
"""
Tests for stats and export API in DB mode using module app.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from dashboard.app import app, _db


def seed_db(tasks: list[dict]) -> None:
  _db.initialize()
  with _db.connect() as conn:
    conn.execute("delete from deps"); conn.execute("delete from now_queue"); conn.execute("delete from tasks")
  for t in tasks:
    _db.create_task(t)


def test_stats_and_export_endpoints_db(tmp_path: Path) -> None:
  app.config['TESTING'] = True
  app.config['API_FORCE_DB'] = True

  tasks = [
    {"id": "X-1", "course": "MATH221", "title": "A", "status": "todo", "category": "setup", "due_at": "2025-08-20"},
    {"id": "X-2", "course": "MATH251", "title": "B", "status": "doing", "category": "content"},
    {"id": "X-3", "course": "MATH221", "title": "C", "status": "done", "category": "assessment", "due_at": "2025-08-25"},
  ]
  seed_db(tasks)

  with app.test_client() as c:
    # Stats
    r = c.get('/api/stats')
    assert r.status_code == 200
    data = r.get_json()
    assert data['total'] == 3 and data['completed'] >= 1

    # JSON export
    rj = c.get('/api/export?format=json')
    assert rj.status_code == 200 and rj.mimetype == 'application/json'
    payload = json.loads(rj.data)
    assert payload['count'] == 3

    # CSV export
    rc = c.get('/api/export?format=csv')
    assert rc.status_code == 200 and 'text/csv' in rc.mimetype

    # ICS export
    ri = c.get('/api/export?format=ics')
    assert ri.status_code == 200 and 'text/calendar' in ri.mimetype
    text = ri.data.decode('utf-8')
    assert 'BEGIN:VCALENDAR' in text
    assert 'BEGIN:VEVENT' in text  # due_at present

