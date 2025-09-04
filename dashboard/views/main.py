#!/usr/bin/env python3
"""
Main web views for the dashboard.
"""

import json
from pathlib import Path

from flask import render_template

from dashboard.config import Config
from dashboard.db import Database, DatabaseConfig
from dashboard.views import main_bp


@main_bp.route("/")
def index() -> str:
    """Main dashboard page."""
    return render_template("dashboard.html")  # type: ignore[no-any-return]


@main_bp.route("/tasks")
def tasks_view() -> str:
    """Tasks list view."""
    db = Database(DatabaseConfig(Config.STATE_DIR / "tasks.db"))
    try:
        db.initialize()
        items = db.list_tasks()
    except Exception:
        items = []
    # Legacy JSON fallback if DB empty and tasks.json present
    if not items:
        try:
            p = Path(Config.STATE_DIR) / "tasks.json"
            if p.exists():
                data = json.loads(p.read_text())
                items = list(data.get("tasks", []))
        except Exception:
            pass
    tasks = {
        "tasks": items,
        "total": len(items),
        "page": 1,
        "per_page": len(items),
        "total_pages": 1,
    }
    return render_template("tasks.html", tasks=tasks)  # type: ignore[no-any-return]


@main_bp.route("/courses")
def courses_view() -> str:
    """Courses overview."""
    return render_template("courses.html")  # type: ignore[no-any-return]
