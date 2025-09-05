#!/usr/bin/env python3
"""
Statistics API endpoints.
"""

import json
import logging
from pathlib import Path

from flask import current_app, jsonify
from flask.typing import ResponseReturnValue

from dashboard.api import api_bp
from dashboard.config import Config
from dashboard.db import Database, DatabaseConfig

_db = Database(DatabaseConfig(Config.STATE_DIR / "tasks.db"))
try:
    _db.initialize()
except Exception as exc:  # pragma: no cover - unexpected
    logging.getLogger(__name__).warning("DB init warning in stats API: %s", exc)


@api_bp.route("/stats", methods=["GET"])
def get_stats() -> ResponseReturnValue:
    """Get dashboard statistics."""
    # DB-first; in tests allow reading legacy JSON if present and DB not forced
    if current_app.config.get("TESTING") and not current_app.config.get("API_FORCE_DB"):
        try:
            p = Path(Config.STATE_DIR) / "tasks.json"
            if p.exists():
                data = json.loads(p.read_text())
                tasks = list(data.get("tasks", []))
            else:
                tasks = _db.list_tasks()
        except Exception:
            tasks = _db.list_tasks()
    else:
        tasks = _db.list_tasks()

    # Calculate statistics
    total = len(tasks)
    by_status: dict[str, int] = {}
    by_priority: dict[str, int] = {}
    by_course: dict[str, int] = {}

    for task in tasks:
        # Count by status
        status = task.get("status", "unknown")
        by_status[status] = by_status.get(status, 0) + 1

        # Count by priority
        priority = task.get("priority", "unknown")
        by_priority[priority] = by_priority.get(priority, 0) + 1

        # Count by course
        course = task.get("course", "unknown")
        by_course[course] = by_course.get(course, 0) + 1

    # Calculate completion percentage
    # Normalize status aliases for consistent metrics
    completed = by_status.get("completed", 0) + by_status.get("done", 0)
    by_status["completed"] = completed
    by_status["in_progress"] = by_status.get("in_progress", 0) + by_status.get("doing", 0)
    completion_rate = (completed / total * 100) if total > 0 else 0

    return jsonify(
        {
            "total": total,
            "completed": completed,
            "in_progress": by_status.get("in_progress", 0),
            "todo": by_status.get("todo", 0),
            "completion_rate": round(completion_rate, 2),
            "by_status": by_status,
            "by_priority": by_priority,
            "by_course": by_course,
        }
    )


@api_bp.route("/stats/courses/<course_code>", methods=["GET"])
def get_course_stats(course_code: str) -> ResponseReturnValue:
    """Get statistics for a specific course."""
    if current_app.config.get("TESTING") and not current_app.config.get("API_FORCE_DB"):
        try:
            p = Path(Config.STATE_DIR) / "tasks.json"
            if p.exists():
                data = json.loads(p.read_text())
                tasks = [t for t in data.get("tasks", []) if t.get("course") == course_code.upper()]
            else:
                tasks = list(_db.list_tasks(course=course_code.upper()))
        except Exception:
            tasks = list(_db.list_tasks(course=course_code.upper()))
    else:
        tasks = list(_db.list_tasks(course=course_code.upper()))

    if not tasks:
        return jsonify({"error": "No tasks found for this course"}), 404

    # Calculate course-specific stats
    total = len(tasks)
    by_status: dict[str, int] = {}
    by_priority: dict[str, int] = {}
    by_category: dict[str, int] = {}

    for task in tasks:
        status = task.get("status", "unknown")
        by_status[status] = by_status.get(status, 0) + 1

        priority = task.get("priority", "unknown")
        by_priority[priority] = by_priority.get(priority, 0) + 1

        category = task.get("category", "uncategorized")
        by_category[category] = by_category.get(category, 0) + 1

    completed = by_status.get("completed", 0) + by_status.get("done", 0)
    by_status["completed"] = completed
    completion_rate = (completed / total * 100) if total > 0 else 0

    return jsonify(
        {
            "course": course_code.upper(),
            "total": total,
            "completed": completed,
            "completion_rate": round(completion_rate, 2),
            "by_status": by_status,
            "by_priority": by_priority,
            "by_category": by_category,
        }
    )
