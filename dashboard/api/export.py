#!/usr/bin/env python3
"""
Export API endpoints for different formats.
"""

import csv
import json
from datetime import datetime
from io import StringIO

from flask import Response, request

from dashboard.api import api_bp
from dashboard.services.task_service import TaskService


@api_bp.route("/export/csv", methods=["GET"])
def export_csv():
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
def export_json():
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

    # Create JSON response
    export_data = {
        "exported_at": datetime.now().isoformat(),
        "filters": {"course": course, "status": status},
        "count": len(tasks),
        "tasks": tasks,
    }

    response = Response(
        json.dumps(export_data, indent=2),
        mimetype="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=tasks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        },
    )

    return response


@api_bp.route("/export/ics", methods=["GET"])
def export_ics():
    """Export tasks as ICS calendar file."""
    # Get filter parameters
    course = request.args.get("course")

    # Get tasks with due dates
    data = TaskService._load_tasks_data()
    tasks = data.get("tasks", [])

    # Filter tasks with due dates
    if course:
        tasks = [t for t in tasks if t.get("course") == course and t.get("due_date")]
    else:
        tasks = [t for t in tasks if t.get("due_date")]

    # Create ICS content
    ics_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Fall 2025 Dashboard//Task Calendar//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]

    for task in tasks:
        due_date = task.get("due_date", "").replace("-", "")
        if len(due_date) == 8:  # YYYYMMDD format
            ics_lines.extend(
                [
                    "BEGIN:VEVENT",
                    f"UID:{task.get('id')}@dashboard.local",
                    f"DTSTART;VALUE=DATE:{due_date}",
                    f"DTEND;VALUE=DATE:{due_date}",
                    f"SUMMARY:[{task.get('course')}] {task.get('title')}",
                    f"DESCRIPTION:{task.get('description', '')}",
                    f"PRIORITY:{_priority_to_ics(task.get('priority', 'medium'))}",
                    f"STATUS:{_status_to_ics(task.get('status', 'todo'))}",
                    "END:VEVENT",
                ]
            )

    ics_lines.append("END:VCALENDAR")

    response = Response(
        "\r\n".join(ics_lines),
        mimetype="text/calendar",
        headers={
            "Content-Disposition": f"attachment; filename=tasks_{datetime.now().strftime('%Y%m%d')}.ics"
        },
    )

    return response


def _priority_to_ics(priority: str) -> int:
    """Convert priority to ICS priority value (1-9, 1 is highest)."""
    mapping = {"critical": 1, "high": 3, "medium": 5, "low": 7}
    return mapping.get(priority, 5)


def _status_to_ics(status: str) -> str:
    """Convert status to ICS status value."""
    mapping = {
        "todo": "NEEDS-ACTION",
        "in_progress": "IN-PROCESS",
        "completed": "COMPLETED",
        "blocked": "CANCELLED",
        "deferred": "TENTATIVE",
    }
    return mapping.get(status, "NEEDS-ACTION")
