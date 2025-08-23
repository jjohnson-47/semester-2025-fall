#!/usr/bin/env python3
"""
Export API endpoints for different formats.
"""

import csv
import json
from datetime import datetime
from io import StringIO

from flask import Response, request
from flask.typing import ResponseReturnValue

from dashboard.api import api_bp
from dashboard.services.task_service import TaskService


@api_bp.route("/export/csv", methods=["GET"])
def export_csv() -> ResponseReturnValue:
    """Export tasks as CSV."""
    # Get filter parameters
    course = request.args.get("course")
    status = request.args.get("status")

    # Get tasks
    data = TaskService._load_tasks_data()
    tasks = data.get("tasks", [])

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
    for task in tasks:
        writer.writerow(task)

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
    data = TaskService._load_tasks_data()
    tasks = data.get("tasks", [])

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
    data = TaskService._load_tasks_data()
    tasks = data.get("tasks", [])

    # Filter tasks with due dates
    if course:
        tasks = [t for t in tasks if t.get("course") == course and t.get("due_date")]
    else:
        tasks = [t for t in tasks if t.get("due_date")]

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
        due_date = task.get("due_date", "")
        status_map = {"todo": "NEEDS-ACTION", "in_progress": "IN-PROCESS", "done": "COMPLETED"}
        status = status_map.get(task.get("status", ""), "NEEDS-ACTION")
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
