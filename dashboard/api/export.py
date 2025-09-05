#!/usr/bin/env python3
"""
Export API endpoints for different formats.
"""

import csv
import json
import logging
from datetime import datetime
from io import StringIO
from pathlib import Path

from flask import Response, current_app, request
from flask.typing import ResponseReturnValue

from dashboard.api import api_bp
from dashboard.config import Config
from dashboard.db import Database, DatabaseConfig

_db = Database(DatabaseConfig(Config.STATE_DIR / "tasks.db"))
try:
    _db.initialize()
except Exception as exc:  # pragma: no cover - unexpected
    logging.getLogger(__name__).warning("DB init warning in export API: %s", exc)


@api_bp.route("/export/csv", methods=["GET"])
def export_csv() -> ResponseReturnValue:
    """Export tasks as CSV."""
    # Get filter parameters
    course = request.args.get("course")
    status = request.args.get("status")

    # Get tasks (testing fallback unless API_FORCE_DB)
    if current_app.config.get("TESTING") and not current_app.config.get("API_FORCE_DB"):
        try:
            p = Path(Config.STATE_DIR) / "tasks.json"
            if p.exists():
                data = json.loads(p.read_text())
                tasks = list(data.get("tasks", []))
            else:
                tasks = _db.list_tasks(status=status, course=course)
        except Exception:
            tasks = _db.list_tasks(status=status, course=course)
    else:
        tasks = _db.list_tasks(status=status, course=course)

    # Apply filters
    if course:
        tasks = [t for t in tasks if t.get("course") == course]
    if status:
        tasks = [t for t in tasks if t.get("status") == status]

    # Create CSV
    output = StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "id",
            "course",
            "title",
            "status",
            "priority",
            "category",
            "due_date",
            "description",
            "created_at",
            "updated_at",
        ],
    )

    writer.writeheader()
    fields = writer.fieldnames or []
    for task in tasks:
        row = {k: task.get(k) for k in fields}
        # Map DB canonical status to legacy names for CSV
        if row.get("status") == "doing":
            row["status"] = "in_progress"
        if row.get("status") == "done":
            row["status"] = "completed"
        # Map due_at to due_date if missing
        if not row.get("due_date") and task.get("due_at"):
            row["due_date"] = task.get("due_at")
        writer.writerow(row)

    # Create response
    response = Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=tasks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        },
    )

    return response


@api_bp.route("/export/json", methods=["GET"])
def export_json() -> ResponseReturnValue:
    """Export tasks as JSON."""
    # Get filter parameters
    course = request.args.get("course")
    status = request.args.get("status")

    # Get tasks
    if current_app.config.get("TESTING") and not current_app.config.get("API_FORCE_DB"):
        try:
            p = Path(Config.STATE_DIR) / "tasks.json"
            if p.exists():
                data = json.loads(p.read_text())
                tasks = list(data.get("tasks", []))
            else:
                tasks = _db.list_tasks(status=status, course=course)
        except Exception:
            tasks = _db.list_tasks(status=status, course=course)
    else:
        tasks = _db.list_tasks(status=status, course=course)

    # Apply filters
    if course:
        tasks = [t for t in tasks if t.get("course") == course]
    if status:
        tasks = [t for t in tasks if t.get("status") == status]

    # Create response
    response = Response(
        json.dumps(
            {"tasks": tasks, "count": len(tasks), "exported_at": datetime.now().isoformat()},
            indent=2,
        ),
        mimetype="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=tasks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        },
    )

    return response


@api_bp.route("/export/ics", methods=["GET"])
def export_ics() -> ResponseReturnValue:
    """Export tasks as iCalendar."""
    # Get filter parameters
    course = request.args.get("course")

    # Get tasks
    if current_app.config.get("TESTING") and not current_app.config.get("API_FORCE_DB"):
        try:
            p = Path(Config.STATE_DIR) / "tasks.json"
            if p.exists():
                data = json.loads(p.read_text())
                tasks = list(data.get("tasks", []))
            else:
                tasks = _db.list_tasks(course=course)
        except Exception:
            tasks = _db.list_tasks(course=course)
    else:
        tasks = _db.list_tasks(course=course)

    # Filter tasks with due dates (support DB 'due_at')
    if course:
        tasks = [
            t for t in tasks if t.get("course") == course and (t.get("due_date") or t.get("due_at"))
        ]
    else:
        tasks = [t for t in tasks if t.get("due_date") or t.get("due_at")]

    # Create iCalendar content
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Dashboard//Task Export//EN",
        "CALSCALE:GREGORIAN",
    ]

    for task in tasks:
        uid = task.get("id", "")
        summary = f"[{task.get('course', '')}] {task.get('title', '')}"
        description = task.get("description", "")
        due_date = task.get("due_date") or task.get("due_at") or ""
        s_in = task.get("status", "")
        if s_in == "doing":
            s_in = "in_progress"
        if s_in == "done":
            s_in = "completed"
        status_map = {"todo": "NEEDS-ACTION", "in_progress": "IN-PROCESS", "completed": "COMPLETED"}
        status = status_map.get(s_in, "NEEDS-ACTION")
        priority_map = {"critical": "1", "high": "3", "medium": "5", "low": "7"}
        priority = priority_map.get(task.get("priority", ""), "5")

        # Format date for iCal
        if due_date:
            try:
                dt = datetime.fromisoformat(due_date)
                due_date_ics = dt.strftime("%Y%m%dT%H%M%S")
            except (ValueError, TypeError):
                continue

            lines.extend(
                [
                    "BEGIN:VEVENT",
                    f"UID:{uid}@dashboard",
                    f"SUMMARY:{summary}",
                    f"DESCRIPTION:{description}",
                    f"DTSTART:{due_date_ics}",
                    f"DTEND:{due_date_ics}",
                    f"STATUS:{status}",
                    f"PRIORITY:{priority}",
                    "END:VEVENT",
                ]
            )

    lines.append("END:VCALENDAR")
    ical_content = "\r\n".join(lines)

    # Create response
    response = Response(
        ical_content,
        mimetype="text/calendar",
        headers={
            "Content-Disposition": f"attachment; filename=tasks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ics"
        },
    )

    return response
