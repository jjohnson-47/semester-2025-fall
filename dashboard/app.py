#!/usr/bin/env python3
"""Course Setup Dashboard - Flask Application.

A comprehensive task management system for semester course preparation that integrates
with the syllabus generation system. Provides a web interface for tracking course
setup tasks, viewing generated syllabi, and managing semester preparation workflow.

Architecture:
    - Flask web framework with Jinja2 templating
    - JSON file-based storage with file locking for concurrent access
    - Environment-based configuration with python-dotenv
    - Integration with build system for syllabus serving
    - Optional git snapshots for state history

Main Components:
    - TaskManager: Core class for task CRUD operations
    - Routes: Dashboard views and API endpoints
    - Templates: Bootstrap-based responsive UI
    - Config: Environment-aware configuration

Usage:
    From project root:
        uv run python dashboard/app.py

    Or using make:
        make dash

Environment Variables:
    DASH_PORT (int): Server port (default: 5055)
    DASH_HOST (str): Server host (default: 127.0.0.1)
    DASH_AUTO_SNAPSHOT (bool): Enable git snapshots (default: true)
    PROJECT_ROOT (str): Project root path (auto-detected)
    BUILD_DIR (str): Build output directory (default: build)
    SYLLABI_DIR (str): Syllabi directory (default: build/syllabi)

See dashboard/API_DOCUMENTATION.md for complete API reference.
"""

import fcntl
import json

# Set up logging
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, cast

import pytz  # type: ignore[import-untyped]
from flask import Flask, Response, jsonify, render_template, request, send_file, send_from_directory
from flask.typing import ResponseReturnValue

from dashboard.config import Config
from dashboard.orchestrator import AgentCoordinator, TaskOrchestrator

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)

# Initialize orchestrator
orchestrator = TaskOrchestrator(state_dir=Config.STATE_DIR)
agent_coordinator = AgentCoordinator(orchestrator)

# Note: The more advanced API is exposed via the package factory in
# dashboard/__init__.py. For this module-level app (used in simpler tests),
# we provide lightweight endpoints implemented against TaskManager.

# Configuration from Config class
TIMEZONE = pytz.timezone(Config.TIMEZONE)
STATE_DIR = Config.STATE_DIR
TASKS_FILE = Config.TASKS_FILE
COURSES_FILE = Config.COURSES_FILE
AUTO_SNAPSHOT = Config.AUTO_SNAPSHOT

# Ensure state directory exists
STATE_DIR.mkdir(exist_ok=True)


class TaskManager:
    """Manages task state with file locking for concurrent access."""

    @staticmethod
    def load_tasks() -> dict[str, Any]:
        """Load tasks with file locking."""
        if not TASKS_FILE.exists():
            return {
                "tasks": [],
                "metadata": {"version": "1.0", "updated": datetime.now().isoformat()},
            }

        with open(TASKS_FILE) as f:
            fcntl.flock(f, fcntl.LOCK_SH)
            try:
                data = json.load(f)
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)
        return dict(data)

    @staticmethod
    def save_tasks(data: dict[str, Any]) -> None:
        """Save tasks with file locking and optional git snapshot."""
        data["metadata"]["updated"] = datetime.now().isoformat()

        with open(TASKS_FILE, "w") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                json.dump(data, f, indent=2)
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)

    @staticmethod
    def update_task_status(task_id: str, status: str) -> bool:
        """Update the status of a specific task."""
        tasks_data = TaskManager.load_tasks()

        for task in tasks_data["tasks"]:
            if task["id"] == task_id:
                task["status"] = status
                task["updated"] = datetime.now().isoformat()
                TaskManager.save_tasks(tasks_data)
                return True

        return False

    @staticmethod
    def load_courses() -> dict[str, Any]:
        """Load courses configuration."""
        if not COURSES_FILE.exists():
            return {"courses": []}

        with open(COURSES_FILE) as f:
            return json.load(f)

    @staticmethod
    def validate_task_data(task: dict[str, Any]) -> bool:
        """Validate task data has required fields."""
        required_fields = ["course", "title", "status", "priority"]
        return all(field in task for field in required_fields)

    @staticmethod
    def git_snapshot() -> None:
        """Create git snapshot of current state."""
        try:
            import subprocess

            subprocess.run(["git", "add", str(TASKS_FILE)], capture_output=True)
            subprocess.run(
                ["git", "commit", "-m", f"dashboard: snapshot {datetime.now().isoformat()}"],
                capture_output=True,
            )
        except Exception:
            pass  # Silently fail if git is not available

    @staticmethod
    def load_courses() -> dict[str, Any]:
        """Load course configuration."""
        if not COURSES_FILE.exists():
            return {"courses": [], "semester": "2025-fall"}

        with open(COURSES_FILE) as f:
            data = json.load(f)
            return dict(data)


def calculate_progress(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    """Calculate overall progress statistics."""
    total = len(tasks)
    if total == 0:
        return {"total": 0, "completed": 0, "percentage": 0}

    completed = sum(1 for t in tasks if t.get("status") == "completed")
    percentage = (completed / total) * 100

    return {"total": total, "completed": completed, "percentage": round(percentage, 2)}


def get_upcoming_deadlines(tasks: list[dict[str, Any]], days: int = 7) -> list[dict[str, Any]]:
    """Get tasks with deadlines in the next N days."""
    upcoming = []
    cutoff_date = datetime.now() + timedelta(days=days)

    for task in tasks:
        if "due_date" in task and task.get("status") != "completed":
            try:
                due_date = datetime.fromisoformat(task["due_date"])
                if due_date <= cutoff_date:
                    upcoming.append(task)
            except (ValueError, TypeError):
                continue

    return sorted(upcoming, key=lambda t: t["due_date"])


def calculate_priority(task: dict[str, Any]) -> int:
    """Calculate task priority based on due date and weight."""
    priority: int = int(task.get("weight", 1))

    if "due" in task:
        try:
            due_date = datetime.fromisoformat(task["due"])
            days_until = (due_date - datetime.now()).days

            if days_until < 0:  # Overdue
                priority += 100
            elif days_until == 0:  # Due today
                priority += 50
            elif days_until <= 3:  # Due soon
                priority += 20
            elif days_until <= 7:  # Due this week
                priority += 10
        except (ValueError, TypeError, AttributeError) as e:
            logger.debug(f"Date parsing error in priority calculation: {e}")
            pass

    return priority


def get_status_color(status: str) -> str:
    """Get color class for status."""
    colors = {
        "blocked": "secondary",
        "todo": "primary",
        "doing": "warning",
        "review": "info",
        "done": "success",
    }
    return colors.get(status, "light")


def get_due_color(task: dict[str, Any]) -> str:
    """Get color class based on due date."""
    if "due" not in task:
        return ""

    try:
        due_date = datetime.fromisoformat(task["due"])
        days_until = (due_date - datetime.now()).days

        if days_until < 0:
            return "danger"  # Overdue
        elif days_until == 0:
            return "warning"  # Due today
        elif days_until <= 3:
            return "info"  # Due soon
        elif days_until <= 7:
            return "primary"  # Due this week
    except (ValueError, TypeError, AttributeError) as e:
        logger.debug(f"Date parsing error in color calculation: {e}")
        pass

    return ""


# Backwards-compatible helper for tests expecting module-level function
def validate_task_data(task: dict[str, Any]) -> bool:
    """Validate task structure (wrapper around TaskManager)."""
    return TaskManager.validate_task_data(task)


@app.route("/")
def index() -> str:
    """Main dashboard view."""
    data = TaskManager.load_tasks()
    courses = TaskManager.load_courses()

    # Load Now Queue if it exists
    now_queue = []
    now_queue_file = STATE_DIR / "now_queue.json"
    if now_queue_file.exists():
        with open(now_queue_file) as f:
            now_queue_data = json.load(f)
            now_queue = now_queue_data.get("queue", [])

    # Calculate priorities and add display helpers
    for task in data["tasks"]:
        # Use smart_score if available, otherwise calculate basic priority
        if "smart_score" not in task:
            task["priority"] = calculate_priority(task)
        else:
            task["priority"] = task["smart_score"]

        task["status_color"] = get_status_color(task.get("status", "todo"))
        task["due_color"] = get_due_color(task)

        # Format due date for display
        if "due_date" in task:
            try:
                due = datetime.fromisoformat(task["due_date"])
                task["due_display"] = due.strftime("%b %d, %Y")
                task["due_relative"] = get_relative_time(due)
            except (ValueError, TypeError, AttributeError) as e:
                logger.debug(f"Failed to format due date for task {task.get('id')}: {e}")
                task["due_display"] = task.get("due_date", "")
        elif "due" in task:  # Fallback for old format
            try:
                due = datetime.fromisoformat(task["due"])
                task["due_display"] = due.strftime("%b %d, %Y")
                task["due_relative"] = get_relative_time(due)
            except (ValueError, TypeError, AttributeError) as e:
                logger.debug(f"Failed to format due date for task {task.get('id')}: {e}")
                task["due_display"] = task["due"]

    # Sort by smart_score/priority
    data["tasks"].sort(key=lambda t: t.get("smart_score", t.get("priority", 0)), reverse=True)

    # Group by course
    by_course: dict[str, list] = {}
    for task in data["tasks"]:
        course = task.get("course", "General")
        if course not in by_course:
            by_course[course] = []
        by_course[course].append(task)

    # Calculate stats
    stats = {
        "total": len(data["tasks"]),
        "blocked": sum(1 for t in data["tasks"] if t.get("status") == "blocked"),
        "todo": sum(1 for t in data["tasks"] if t.get("status") == "todo"),
        "doing": sum(1 for t in data["tasks"] if t.get("status") == "doing"),
        "review": sum(1 for t in data["tasks"] if t.get("status") == "review"),
        "done": sum(1 for t in data["tasks"] if t.get("status") == "done"),
        "overdue": sum(1 for t in data["tasks"] if t.get("due_color") == "danger"),
    }

    return cast(
        str,
        render_template(
            "dashboard.html",
            tasks=data["tasks"],
            by_course=by_course,
            courses=courses.get("courses", []),
            stats=stats,
            updated=data["metadata"].get("updated"),
            now_queue=now_queue,
        ),
    )


# --- Lightweight JSON API (TaskManager-backed) ---
@app.route("/api/tasks", methods=["GET"])
def api_get_tasks() -> ResponseReturnValue:
    """Return tasks with optional filtering by course and status."""
    data = TaskManager.load_tasks()
    tasks = data.get("tasks", [])

    course = request.args.get("course")
    status = request.args.get("status")

    if course:
        tasks = [t for t in tasks if t.get("course") == course]
    if status:
        tasks = [t for t in tasks if t.get("status") == status]

    return jsonify({"tasks": tasks, "metadata": data.get("metadata", {})})


@app.route("/api/tasks", methods=["POST"])
def api_create_task() -> ResponseReturnValue:
    """Create a new task and persist it to state."""
    payload = request.get_json(silent=True) or {}
    required = ["course", "title", "status", "priority"]
    missing = [f for f in required if f not in payload]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    data = TaskManager.load_tasks()
    tasks = data.setdefault("tasks", [])

    # Generate a simple ID if not provided
    task_id = payload.get("id")
    if not task_id:
        base = f"{payload['course']}-{len(tasks)+1:03d}"
        # Ensure uniqueness
        existing_ids = {t.get("id") for t in tasks}
        i = 1
        candidate = base
        while candidate in existing_ids:
            i += 1
            candidate = f"{base}-{i}"
        task_id = candidate
    payload["id"] = task_id

    tasks.append(payload)
    TaskManager.save_tasks(data)

    return jsonify({"id": task_id}), 201


@app.route("/api/tasks/<task_id>", methods=["PUT"])
def api_update_task(task_id: str) -> ResponseReturnValue:
    """Update a task's status. Expects JSON: {"status": "..."}."""
    body = request.get_json(silent=True) or {}
    new_status = body.get("status")
    if not new_status:
        return jsonify({"error": "Missing 'status' in request body"}), 400

    updated = TaskManager.update_task_status(task_id, new_status)
    if not updated:
        return jsonify({"error": "Task not found"}), 404

    # Return updated task payload for parity with API blueprint
    data = TaskManager.load_tasks()
    task = next((t for t in data.get("tasks", []) if t.get("id") == task_id), None)
    return jsonify({"success": True, "task": task})


@app.route("/api/stats", methods=["GET"])
def api_stats() -> ResponseReturnValue:
    """Return basic task statistics for dashboard tests."""
    data = TaskManager.load_tasks()
    tasks = data.get("tasks", [])

    stats = {
        "total": len(tasks),
        "completed": sum(1 for t in tasks if t.get("status") == "completed"),
        "in_progress": sum(1 for t in tasks if t.get("status") == "in_progress"),
        "todo": sum(1 for t in tasks if t.get("status") == "todo"),
    }

    return jsonify(stats)


@app.route("/api/tasks/bulk-update", methods=["POST"])
def api_bulk_update() -> ResponseReturnValue:
    """Bulk update tasks matching simple filter criteria.

    Expected body: {"filter": {...}, "update": {...}}
    Matches on equality for provided filter fields.
    """
    body = request.get_json(silent=True) or {}
    if "filter" not in body or "update" not in body:
        return jsonify({"error": "Missing filter or update parameters"}), 400

    filter_params = body["filter"] or {}
    update_params = body["update"] or {}

    data = TaskManager.load_tasks()
    tasks = data.get("tasks", [])

    updated_count = 0
    for task in tasks:
        if all(task.get(k) == v for k, v in filter_params.items()):
            task.update(update_params)
            task["updated"] = datetime.now().isoformat()
            updated_count += 1

    if updated_count:
        TaskManager.save_tasks(data)

    return jsonify({"success": True, "updated_count": updated_count})


@app.route("/api/export", methods=["GET"])
def api_export() -> ResponseReturnValue:
    """Export tasks in CSV, JSON, or ICS format.

    Query params: format=csv|json|ics, optional course, status filters.
    """
    export_format = (request.args.get("format", "csv") or "csv").lower()
    course = request.args.get("course")
    status = request.args.get("status")

    data = TaskManager.load_tasks()
    tasks = data.get("tasks", [])

    if course:
        tasks = [t for t in tasks if t.get("course") == course]
    if status:
        tasks = [t for t in tasks if t.get("status") == status]

    if export_format == "json":
        payload = {
            "exported_at": datetime.now().isoformat(),
            "filters": {"course": course, "status": status},
            "count": len(tasks),
            "tasks": tasks,
        }
        return Response(
            json.dumps(payload, indent=2),
            mimetype="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=tasks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            },
        )

    if export_format == "csv":
        import csv
        from io import StringIO

        output = StringIO()
        fieldnames = [
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
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for task in tasks:
            writer.writerow(task)

        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=tasks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            },
        )

    if export_format == "ics":

        def _priority_to_ics(priority: str) -> int:
            mapping = {"critical": 1, "high": 3, "medium": 5, "low": 7}
            return mapping.get(priority, 5)

        def _status_to_ics(status_value: str) -> str:
            mapping = {
                "todo": "NEEDS-ACTION",
                "in_progress": "IN-PROCESS",
                "completed": "COMPLETED",
                "blocked": "CANCELLED",
                "deferred": "TENTATIVE",
            }
            return mapping.get(status_value, "NEEDS-ACTION")

        ics_lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Dashboard//Task Calendar//EN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
        ]

        for task in tasks:
            due = (task.get("due_date") or "").replace("-", "")
            if len(due) == 8:  # YYYYMMDD
                ics_lines.extend(
                    [
                        "BEGIN:VEVENT",
                        f"UID:{task.get('id')}@dashboard.local",
                        f"DTSTART;VALUE=DATE:{due}",
                        f"DTEND;VALUE=DATE:{due}",
                        f"SUMMARY:[{task.get('course')}] {task.get('title')}",
                        f"DESCRIPTION:{task.get('description', '')}",
                        f"PRIORITY:{_priority_to_ics(task.get('priority', 'medium'))}",
                        f"STATUS:{_status_to_ics(task.get('status', 'todo'))}",
                        "END:VEVENT",
                    ]
                )

        ics_lines.append("END:VCALENDAR")

        return Response(
            "\r\n".join(ics_lines),
            mimetype="text/calendar",
            headers={
                "Content-Disposition": f"attachment; filename=tasks_{datetime.now().strftime('%Y%m%d')}.ics"
            },
        )

    return jsonify({"error": f"Unsupported format: {export_format}"}), 400


@app.route("/api/task/<task_id>", methods=["GET", "POST"])
def api_task(task_id: str) -> ResponseReturnValue:
    """API endpoint for task operations."""
    data = TaskManager.load_tasks()

    # Find task
    task = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            task = t
            break

    if not task:
        return jsonify({"error": "Task not found"}), 404

    if request.method == "POST":
        # Update task
        updates = request.json

        # Track history
        if "history" not in task:
            task["history"] = []

        # Update fields
        for key, value in updates.items():
            if key in ["status", "notes", "checklist"]:
                old_value = task.get(key)
                task[key] = value

                # Add to history
                task["history"].append(
                    {"at": datetime.now().isoformat(), "field": key, "from": old_value, "to": value}
                )

        # Check dependencies
        if task.get("status") == "done":
            # Unblock dependent tasks
            for other in data["tasks"]:
                if "blocked_by" in other and task_id in other["blocked_by"]:
                    other["blocked_by"].remove(task_id)
                    if not other["blocked_by"] and other.get("status") == "blocked":
                        other["status"] = "todo"

        TaskManager.save_tasks(data)
        return jsonify({"success": True, "task": task})

    return jsonify(task)


@app.route("/api/tasks/bulk", methods=["POST"])
def api_bulk_update_tasks_list() -> ResponseReturnValue:
    """Bulk update tasks."""
    data = TaskManager.load_tasks()
    updates = request.json

    updated_count = 0
    for task_update in updates.get("tasks", []):
        task_id = task_update.get("id")
        for task in data["tasks"]:
            if task["id"] == task_id:
                for key, value in task_update.items():
                    if key != "id":
                        task[key] = value
                updated_count += 1
                break

    TaskManager.save_tasks(data)
    return jsonify({"success": True, "updated": updated_count})


@app.route("/view/<view_name>")
def filtered_view(view_name: str) -> str:
    """Filtered views (today, week, overdue, etc.)."""
    data = TaskManager.load_tasks()

    filtered_tasks = []
    now = datetime.now()

    if view_name == "today":
        for task in data["tasks"]:
            if "due" in task:
                try:
                    due = datetime.fromisoformat(task["due"])
                    if due.date() == now.date():
                        filtered_tasks.append(task)
                except (ValueError, TypeError, AttributeError) as e:
                    logger.debug(f"Invalid date in filtered view: {e}")
                    continue

    elif view_name == "week":
        week_end = now + timedelta(days=7)
        for task in data["tasks"]:
            if "due" in task:
                try:
                    due = datetime.fromisoformat(task["due"])
                    if now <= due <= week_end:
                        filtered_tasks.append(task)
                except (ValueError, TypeError, AttributeError) as e:
                    logger.debug(f"Invalid date in filtered view: {e}")
                    continue

    elif view_name == "overdue":
        for task in data["tasks"]:
            if "due" in task and task.get("status") != "done":
                try:
                    due = datetime.fromisoformat(task["due"])
                    if due < now:
                        filtered_tasks.append(task)
                except (ValueError, TypeError, AttributeError) as e:
                    logger.debug(f"Invalid date in filtered view: {e}")
                    continue

    elif view_name == "blocked":
        filtered_tasks = [t for t in data["tasks"] if t.get("status") == "blocked"]

    elif view_name == "doing":
        filtered_tasks = [t for t in data["tasks"] if t.get("status") == "doing"]

    # Add display helpers
    for task in filtered_tasks:
        task["priority"] = calculate_priority(task)
        task["status_color"] = get_status_color(task.get("status", "todo"))
        task["due_color"] = get_due_color(task)

        if "due" in task:
            try:
                due = datetime.fromisoformat(task["due"])
                task["due_display"] = due.strftime("%b %d, %Y")
                task["due_relative"] = get_relative_time(due)
            except (ValueError, TypeError, AttributeError) as e:
                logger.debug(f"Failed to format due date for task {task.get('id')}: {e}")
                task["due_display"] = task["due"]

    filtered_tasks.sort(key=lambda t: t["priority"], reverse=True)

    return cast(
        str,
        render_template(
            "filtered.html",
            tasks=filtered_tasks,
            view_name=view_name.title(),
            count=len(filtered_tasks),
        ),
    )


def get_relative_time(dt: datetime) -> str:
    """Get human-readable relative time."""
    now = datetime.now()
    if dt.tzinfo is None:
        dt = TIMEZONE.localize(dt)
    if now.tzinfo is None:
        now = TIMEZONE.localize(now)

    diff = dt - now
    days = diff.days

    if days < -1:
        return f"{-days} days overdue"
    elif days == -1:
        return "1 day overdue"
    elif days == 0:
        return "Due today"
    elif days == 1:
        return "Due tomorrow"
    elif days <= 7:
        return f"Due in {days} days"
    else:
        return f"Due in {days} days"


@app.route("/preview")
def syllabus_preview() -> str:
    """Enhanced syllabus preview page."""
    courses = TaskManager.load_courses().get("courses", [])
    return render_template("syllabus_preview.html", courses=courses)  # type: ignore[no-any-return]


@app.route("/api/schedule/<course_code>")
def get_schedule_html(course_code: str) -> ResponseReturnValue:
    """Get schedule as HTML for preview."""
    import markdown as md  # type: ignore[import-untyped]

    schedule_dir = Config.BUILD_DIR / "schedules"
    schedule_path = schedule_dir / f"{course_code}_schedule.md"

    if not schedule_path.exists():
        return jsonify({"error": "Schedule not found"}), 404

    # Read and convert markdown to HTML
    with open(schedule_path) as f:
        markdown_content = f.read()

    # Convert to HTML with tables extension
    html_content = md.markdown(markdown_content, extensions=["tables", "fenced_code", "nl2br"])

    # Wrap in Bootstrap-styled container
    styled_html = f"""
    <div class="container-fluid p-4">
        <style>
            table {{
                width: 100%;
                margin: 1rem 0;
            }}
            table, th, td {{
                border: 1px solid #dee2e6;
                border-collapse: collapse;
            }}
            th, td {{
                padding: 0.75rem;
                text-align: left;
            }}
            th {{
                background-color: #f8f9fa;
                font-weight: 600;
            }}
            tr:hover {{
                background-color: #f8f9fa;
            }}
            h1, h2, h3 {{
                color: #495057;
                margin-top: 1.5rem;
                margin-bottom: 1rem;
            }}
            ul, ol {{
                margin-left: 1.5rem;
            }}
            code {{
                background: #f8f9fa;
                padding: 0.2rem 0.4rem;
                border-radius: 3px;
            }}
        </style>
        {html_content}
    </div>
    """

    return styled_html


@app.route("/api/schedule/build/<course_code>", methods=["POST"])
def build_schedule(course_code: str) -> ResponseReturnValue:
    """Build schedule for a course."""
    from scripts.build_schedules import ScheduleBuilder

    try:
        builder = ScheduleBuilder(output_dir="build/schedules")
        schedule_path = builder.build_schedule(course_code)
        return jsonify({"success": True, "path": str(schedule_path)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/syllabus/pdf/<course_code>")
@app.route("/api/syllabus/pdf/<course_code>_with_calendar")
def download_syllabus_pdf(course_code: str) -> ResponseReturnValue:
    """Download syllabus as PDF."""
    from flask import abort, send_file

    # Determine if with_calendar variant is requested
    variant = "_with_calendar" if request.path.endswith("_with_calendar") else ""
    course_code = course_code.replace("_with_calendar", "")

    # Check if PDF exists
    pdf_dir = Config.BUILD_DIR / "syllabi" / "pdf"
    pdf_path = pdf_dir / f"{course_code}{variant}.pdf"

    if not pdf_path.exists():
        # Try to generate it
        try:
            from scripts.build_syllabi import SyllabusBuilder

            builder = SyllabusBuilder()
            builder.build_syllabus(course_code)
        except Exception as e:
            abort(404, f"PDF not available: {e}")

    if pdf_path.exists():
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=f"{course_code}_syllabus{variant}.pdf",
            mimetype="application/pdf",
        )
    else:
        abort(404, "PDF not found")


@app.route("/css/<path:filename>")
def serve_css(filename: str) -> ResponseReturnValue:
    """Serve CSS files from build/css directory using Flask's send_from_directory."""
    css_directory = Config.BUILD_DIR / "css"
    try:
        return send_from_directory(css_directory, filename, mimetype="text/css")
    except FileNotFoundError:
        return "CSS file not found", 404


@app.route("/schedules/<course_code>")
def view_schedule(course_code: str) -> ResponseReturnValue:
    """Serve HTML schedule for a course."""
    schedule_file = Path(Config.BUILD_DIR) / "schedules" / f"{course_code}_schedule.html"

    if not schedule_file.exists():
        # Try to build it
        result = subprocess.run(
            [
                "python",
                "scripts/build_schedules.py",
                "--course",
                course_code,
                "--output",
                "build/schedules",
            ],
            capture_output=True,
            text=True,
        )

        if not schedule_file.exists():
            return f"Schedule not found for {course_code}", 404

    return send_file(schedule_file)


@app.route("/syllabi/<course_code>")
def view_syllabus(course_code: str) -> ResponseReturnValue:
    """Serve generated syllabus for a course."""
    from flask import abort, send_from_directory

    # Use configured paths
    syllabi_dir = Config.SYLLABI_DIR

    # Try HTML first, then Markdown
    variant = (request.args.get("variant") or "").strip().lower()
    base_name = f"{course_code}_with_calendar" if variant == "with_calendar" else course_code
    html_path = syllabi_dir / f"{base_name}.html"
    md_path = syllabi_dir / f"{base_name}.md"

    if html_path.exists():
        return send_from_directory(str(syllabi_dir), f"{course_code}.html")
    elif md_path.exists():
        # Read markdown and render it with basic HTML wrapper
        with open(md_path) as f:
            md_content = f.read()

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{course_code} Syllabus</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                body {{ padding: 20px; max-width: 900px; margin: 0 auto; }}
                pre {{ background: #f5f5f5; padding: 10px; border-radius: 5px; }}
                table {{ width: 100%; margin: 20px 0; }}
                th, td {{ padding: 8px; border: 1px solid #ddd; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="mb-3">
                <a href="/" class="btn btn-sm btn-secondary">← Back to Dashboard</a>
            </div>
            <pre>{md_content}</pre>
        </body>
        </html>
        """
        return html_content
    else:
        abort(
            404,
            f"Syllabus not found for {course_code}{' (with calendar)' if variant=='with_calendar' else ''}",
        )


@app.template_filter("status_icon")
def status_icon(status: str) -> str:
    """Get icon for status."""
    icons = {"blocked": "🚫", "todo": "📋", "doing": "⚡", "review": "👀", "done": "✅"}
    return icons.get(status, "❓")


# Iframe hosting routes for Blackboard Ultra integration
@app.route("/embed/syllabus/<course_code>")
def embed_syllabus(course_code: str) -> str:
    """Serve syllabus optimized for iframe embedding with CORS headers."""
    syllabus_path = Path(f"build/syllabi/{course_code}.html")

    if syllabus_path.exists():
        with open(syllabus_path, encoding="utf-8") as f:
            content = f.read()

        # Add iframe-optimized styling
        iframe_style = """
        <style>
            body {
                margin: 0;
                padding: 15px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                line-height: 1.6;
            }
            .container { max-width: 100%; }
            @media print { body { padding: 0; } }
        </style>
        """

        # Insert style before </head>
        content = content.replace("</head>", f"{iframe_style}</head>")

        response = Response(content, mimetype="text/html")
        response.headers["X-Frame-Options"] = "ALLOWALL"
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Content-Security-Policy"] = "frame-ancestors *;"

        return response

    return "Syllabus not found", 404


@app.route("/embed/schedule/<course_code>")
def embed_schedule(course_code: str) -> str:
    """Serve course schedule optimized for iframe embedding."""
    schedule_path = Path(f"build/schedules/{course_code}.html")

    if schedule_path.exists():
        with open(schedule_path, encoding="utf-8") as f:
            content = f.read()

        # Add iframe-optimized styling
        iframe_style = """
        <style>
            body {
                margin: 0;
                padding: 15px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 10px;
            }
            th, td {
                padding: 8px;
                border: 1px solid #ddd;
                text-align: left;
            }
            th {
                background-color: #f8f9fa;
                font-weight: 600;
            }
            tr:hover { background-color: #f5f5f5; }
            @media (max-width: 768px) {
                body { padding: 10px; }
                th, td { padding: 5px; font-size: 14px; }
            }
        </style>
        """

        content = content.replace("</head>", f"{iframe_style}</head>")

        response = Response(content, mimetype="text/html")
        response.headers["X-Frame-Options"] = "ALLOWALL"
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Content-Security-Policy"] = "frame-ancestors *;"

        return response

    return "Schedule not found", 404


@app.route("/embed/generator")
def embed_generator() -> str:
    """Generate iframe embed codes for Blackboard Ultra."""
    courses_data = TaskManager.load_courses()
    courses = [c["code"] for c in courses_data.get("courses", [])]
    if not courses:  # Fallback
        courses = ["MATH221", "MATH251", "STAT253"]

    # Use public URL for iframe generation instead of local dev server
    base_url = Config.PUBLIC_BASE_URL

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Blackboard Ultra Embed Code Generator</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            .code-block {{
                background: #f5f5f5;
                padding: 15px;
                border-radius: 5px;
                font-family: 'Courier New', monospace;
                font-size: 14px;
                margin: 10px 0;
                position: relative;
            }}
            .copy-btn {{
                position: absolute;
                top: 10px;
                right: 10px;
            }}
            .copied {{
                background-color: #28a745 !important;
                border-color: #28a745 !important;
            }}
        </style>
    </head>
    <body>
        <div class="container mt-4">
            <h1>Blackboard Ultra Embed Code Generator</h1>
            <p class="lead">Copy and paste these iframe codes into Blackboard Ultra's HTML editor</p>

            <div class="alert alert-info">
                <h5><i class="bi bi-info-circle"></i> How to Use in Blackboard Ultra</h5>
                <ol>
                    <li>In Blackboard Ultra, create a new Content Item or edit existing</li>
                    <li>Choose "Create" → "Document" or similar content type</li>
                    <li>Click the HTML source button (&lt;/&gt;) in the editor toolbar</li>
                    <li>Paste the iframe code below</li>
                    <li>Click "Save" - content will appear with proper CORS headers</li>
                    <li><strong>Note:</strong> iframes show live content from your server</li>
                </ol>
                <div class="mt-2">
                    <strong>Public URL:</strong> <code>{base_url}</code><br>
                    <small class="text-muted">iframes will load content from your production Cloudflare Pages deployment.</small>
                    <br><small class="text-warning"><i class="bi bi-exclamation-triangle"></i> Ensure content is deployed to production before using these codes!</small>
                </div>
            </div>
    """

    for course in courses:
        html += f"""
            <div class="card mb-4">
                <div class="card-header">
                    <h3>{course}</h3>
                </div>
                <div class="card-body">
                    <h5>Syllabus Embed Code:</h5>
                    <div class="code-block">
                        <button class="btn btn-sm btn-primary copy-btn" onclick="copyCode(this, 'syllabus-{course}')">Copy</button>
                        <code id="syllabus-{course}">&lt;iframe src="{base_url}/courses/{course}/fall-2025/syllabus/embed/"
    width="100%"
    height="800"
    frameborder="0"
    style="border: 1px solid #ddd; border-radius: 4px;"
    title="{course} Syllabus"&gt;&lt;/iframe&gt;</code>
                    </div>

                    <h5>Schedule Embed Code:</h5>
                    <div class="code-block">
                        <button class="btn btn-sm btn-primary copy-btn" onclick="copyCode(this, 'schedule-{course}')">Copy</button>
                        <code id="schedule-{course}">&lt;iframe src="{base_url}/courses/{course}/fall-2025/schedule/embed/"
    width="100%"
    height="600"
    frameborder="0"
    style="border: 1px solid #ddd; border-radius: 4px;"
    title="{course} Schedule"&gt;&lt;/iframe&gt;</code>
                    </div>

                    <div class="row mt-3">
                        <div class="col">
                            <a href="{base_url}/courses/{course}/fall-2025/syllabus/embed/" target="_blank" class="btn btn-outline-primary">
                                Preview Syllabus
                            </a>
                        </div>
                        <div class="col">
                            <a href="{base_url}/courses/{course}/fall-2025/schedule/embed/" target="_blank" class="btn btn-outline-primary">
                                Preview Schedule
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        """

    html += """
        </div>
        <script>
            function copyCode(btn, codeId) {
                const code = document.getElementById(codeId).textContent;
                navigator.clipboard.writeText(code).then(() => {
                    btn.textContent = 'Copied!';
                    btn.classList.add('copied');
                    setTimeout(() => {
                        btn.textContent = 'Copy';
                        btn.classList.remove('copied');
                    }, 2000);
                });
            }
        </script>
    </body>
    </html>
    """

    return html


@app.route("/api/syllabus/download/<course_code>.<format>")
def download_syllabus(course_code: str, format: str) -> ResponseReturnValue:
    """Download syllabus as HTML or DOCX."""
    import subprocess
    import tempfile
    
    if format not in ["html", "docx"]:
        return jsonify({"error": "Invalid format. Use 'html' or 'docx'"}), 400
    
    # Get variant from query parameter
    variant = request.args.get('variant', 'embed')
    
    # Get the HTML file from site directory (production-ready version)
    if variant == 'with_calendar':
        html_path = Config.PROJECT_ROOT / "site" / "courses" / course_code / "fall-2025" / "syllabus" / "index.html"
    else:
        html_path = Config.PROJECT_ROOT / "site" / "courses" / course_code / "fall-2025" / "syllabus" / "embed" / "index.html"
    
    if not html_path.exists():
        return jsonify({"error": "Syllabus HTML not found. Try rebuilding site."}), 404
    
    if format == "html":
        # Return the HTML file directly
        return send_file(
            html_path,
            as_attachment=True,
            download_name=f"{course_code}_syllabus_fall2025.html",
            mimetype="text/html"
        )
    
    elif format == "docx":
        # Convert HTML to DOCX using pandoc
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp_docx:
            try:
                # Use pandoc to convert HTML to DOCX
                cmd = [
                    "pandoc",
                    str(html_path),
                    "-f", "html",
                    "-t", "docx",
                    "-o", tmp_docx.name
                ]
                
                # Add reference doc if it exists
                ref_doc = Config.PROJECT_ROOT / "assets" / "reference.docx"
                if ref_doc.exists():
                    cmd.extend(["--reference-doc", str(ref_doc)])
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=Config.PROJECT_ROOT
                )
                
                if result.returncode != 0:
                    return jsonify({"error": f"Pandoc conversion failed: {result.stderr}"}), 500
                
                # Send the DOCX file
                return send_file(
                    tmp_docx.name,
                    as_attachment=True,
                    download_name=f"{course_code}_syllabus_fall2025.docx",
                    mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
            finally:
                # Clean up temp file after sending
                import os
                if os.path.exists(tmp_docx.name):
                    os.unlink(tmp_docx.name)


@app.route("/api/schedule/download/<course_code>.<format>")
def download_schedule(course_code: str, format: str) -> ResponseReturnValue:
    """Download schedule as HTML or DOCX."""
    import subprocess
    import tempfile
    
    if format not in ["html", "docx"]:
        return jsonify({"error": "Invalid format. Use 'html' or 'docx'"}), 400
    
    # Build the schedule first to ensure it's up to date
    from scripts.build_schedules import ScheduleBuilder
    try:
        builder = ScheduleBuilder(output_dir="build/schedules")
        builder.build_schedule(course_code)
    except Exception as e:
        return jsonify({"error": f"Failed to build schedule: {str(e)}"}), 500
    
    # Get the HTML file from site directory (production-ready version)
    html_path = Config.PROJECT_ROOT / "site" / "courses" / course_code / "fall-2025" / "schedule" / "index.html"
    
    if not html_path.exists():
        # Try embed version
        html_path = Config.PROJECT_ROOT / "site" / "courses" / course_code / "fall-2025" / "schedule" / "embed" / "index.html"
    
    if not html_path.exists():
        return jsonify({"error": "Schedule HTML not found. Try rebuilding site."}), 404
    
    if format == "html":
        # Return the HTML file directly
        return send_file(
            html_path,
            as_attachment=True,
            download_name=f"{course_code}_schedule_fall2025.html",
            mimetype="text/html"
        )
    
    elif format == "docx":
        # Convert HTML to DOCX using pandoc
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp_docx:
            try:
                # Use pandoc to convert HTML to DOCX
                cmd = [
                    "pandoc",
                    str(html_path),
                    "-f", "html",
                    "-t", "docx",
                    "-o", tmp_docx.name
                ]
                
                # Add reference doc if it exists
                ref_doc = Config.PROJECT_ROOT / "assets" / "reference.docx"
                if ref_doc.exists():
                    cmd.extend(["--reference-doc", str(ref_doc)])
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=Config.PROJECT_ROOT
                )
                
                if result.returncode != 0:
                    return jsonify({"error": f"Pandoc conversion failed: {result.stderr}"}), 500
                
                # Send the DOCX file
                return send_file(
                    tmp_docx.name,
                    as_attachment=True,
                    download_name=f"{course_code}_schedule_fall2025.docx",
                    mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
            finally:
                # Clean up temp file after sending
                import os
                if os.path.exists(tmp_docx.name):
                    os.unlink(tmp_docx.name)


@app.route("/api/export/docx")
def export_docx() -> ResponseReturnValue:
    """Export all syllabi and schedules as DOCX files using pandoc."""
    import subprocess
    import tempfile
    import zipfile

    try:
        # Create temporary directory for DOCX files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            zip_path = temp_path / "course_materials.zip"

            # Get course codes
            courses_data = TaskManager.load_courses()
            course_codes = [c["code"] for c in courses_data.get("courses", [])]

            # Create ZIP file with all DOCX exports
            with zipfile.ZipFile(zip_path, "w") as zip_file:
                for course_code in course_codes:
                    # Convert syllabus to DOCX
                    syllabus_html = Config.SYLLABI_DIR / f"{course_code}.html"
                    if syllabus_html.exists():
                        syllabus_docx = temp_path / f"{course_code}_syllabus.docx"
                        subprocess.run(
                            [
                                "pandoc",
                                str(syllabus_html),
                                "-o",
                                str(syllabus_docx),
                                "--from=html",
                                "--to=docx",
                            ],
                            check=True,
                        )
                        zip_file.write(syllabus_docx, f"{course_code}_syllabus.docx")

                    # Convert schedule to DOCX if it exists
                    schedule_html = Config.SCHEDULES_DIR / f"{course_code}.html"
                    if schedule_html.exists():
                        schedule_docx = temp_path / f"{course_code}_schedule.docx"
                        subprocess.run(
                            [
                                "pandoc",
                                str(schedule_html),
                                "-o",
                                str(schedule_docx),
                                "--from=html",
                                "--to=docx",
                            ],
                            check=True,
                        )
                        zip_file.write(schedule_docx, f"{course_code}_schedule.docx")

                # Create combined document for admin
                combined_html = temp_path / "combined.html"
                with open(combined_html, "w") as f:
                    f.write(
                        "<html><head><title>All Course Materials - Fall 2025</title></head><body>"
                    )
                    f.write("<h1>Course Materials - Fall 2025</h1>")

                    for course_code in course_codes:
                        syllabus_html = Config.SYLLABI_DIR / f"{course_code}.html"
                        schedule_html = Config.SCHEDULES_DIR / f"{course_code}.html"

                        f.write(f"<h2>{course_code}</h2>")

                        if syllabus_html.exists():
                            f.write(f"<h3>{course_code} Syllabus</h3>")
                            f.write(syllabus_html.read_text())
                            f.write("<div style='page-break-after: always;'></div>")

                        if schedule_html.exists():
                            f.write(f"<h3>{course_code} Schedule</h3>")
                            f.write(schedule_html.read_text())
                            f.write("<div style='page-break-after: always;'></div>")

                    f.write("</body></html>")

                # Convert combined document to DOCX
                combined_docx = temp_path / "combined_all_courses.docx"
                subprocess.run(
                    [
                        "pandoc",
                        str(combined_html),
                        "-o",
                        str(combined_docx),
                        "--from=html",
                        "--to=docx",
                    ],
                    check=True,
                )
                zip_file.write(combined_docx, "combined_all_courses.docx")

            return send_file(
                zip_path,
                as_attachment=True,
                download_name="course_materials_fall2025.zip",
                mimetype="application/zip",
            )

    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"Pandoc conversion failed: {e}"}), 500
    except Exception as e:
        return jsonify({"error": f"Export failed: {e}"}), 500


@app.route("/api/site/preview/start", methods=["POST"])
def start_site_preview():
    """Start the local site preview server."""
    try:
        import subprocess
        import threading
        
        def run_server():
            # Start the site preview server in the background
            subprocess.Popen([
                "python", "-m", "http.server", "8000",
                "-d", str(Config.PROJECT_ROOT / "site")
            ])
        
        # Start server in a separate thread
        threading.Thread(target=run_server, daemon=True).start()
        
        return jsonify({"success": True, "message": "Site preview server starting at http://localhost:8000"})
        
    except Exception as e:
        logger.error(f"Error starting site preview: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/orchestrate", methods=["POST"])
def api_orchestrate() -> ResponseReturnValue:
    """Analyze and orchestrate task execution."""
    data = TaskManager.load_tasks()
    tasks = data.get("tasks", [])

    # Analyze task graph
    analysis = orchestrator.analyze_task_graph(tasks)

    # Get suggestions for next tasks
    completed = [t["id"] for t in tasks if t.get("status") == "done"]
    available = [t for t in tasks if t.get("status") in ["todo", "blocked"]]
    suggestions = orchestrator.suggest_next_tasks(completed, available)

    # Convert sets to lists for JSON serialization
    if "parallel_groups" in analysis:
        analysis["parallel_groups"] = [list(group) for group in analysis["parallel_groups"]]

    return jsonify(
        {
            "analysis": analysis,
            "suggestions": [{"task_id": tid, "confidence": score} for tid, score in suggestions],
            "agent_status": agent_coordinator.get_agent_status(),
        }
    )


@app.route("/api/agent/register", methods=["POST"])
def api_register_agent() -> ResponseReturnValue:
    """Register a new agent with capabilities."""
    body = request.get_json(silent=True) or {}
    agent_id = body.get("agent_id")
    capabilities = body.get("capabilities", [])

    if not agent_id:
        return jsonify({"error": "Missing agent_id"}), 400

    agent_coordinator.register_agent(agent_id, capabilities)

    return jsonify({"success": True, "agent_id": agent_id})


@app.route("/api/agent/assign", methods=["POST"])
def api_assign_task() -> ResponseReturnValue:
    """Assign a task to an available agent."""
    body = request.get_json(silent=True) or {}
    task_id = body.get("task_id")

    if not task_id:
        return jsonify({"error": "Missing task_id"}), 400

    # Load task data
    data = TaskManager.load_tasks()
    task = next((t for t in data.get("tasks", []) if t["id"] == task_id), None)

    if not task:
        return jsonify({"error": "Task not found"}), 404

    assigned_agent = agent_coordinator.assign_task(task)

    if assigned_agent:
        return jsonify({"success": True, "agent_id": assigned_agent})
    else:
        return jsonify({"error": "No available agent for task"}), 503


if __name__ == "__main__":
    port = int(os.environ.get("DASH_PORT", 5055))
    host = os.environ.get("DASH_HOST", "127.0.0.1")
    debug_mode = os.environ.get("FLASK_ENV", "development") == "development"
    app.run(host=host, port=port, debug=debug_mode)
