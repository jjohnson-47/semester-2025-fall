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
from typing import Any

import pytz
from flask import Flask, Response, jsonify, render_template, request

# Import config - try both relative and absolute imports
try:
    from config import Config
except ImportError:
    from dashboard.config import Config

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)

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
        return data

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
            return json.load(f)


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
    priority = task.get("weight", 1)

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
def index():
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
    by_course = {}
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

    return render_template(
        "dashboard.html",
        tasks=data["tasks"],
        by_course=by_course,
        courses=courses.get("courses", []),
        stats=stats,
        updated=data["metadata"].get("updated"),
        now_queue=now_queue,
    )


# --- Lightweight JSON API (TaskManager-backed) ---
@app.route("/api/tasks", methods=["GET"])
def api_get_tasks():
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
def api_create_task():
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
def api_update_task(task_id: str):
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
def api_stats():
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
def api_bulk_update() -> Response:
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
def api_export() -> Response:
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
def api_task(task_id):
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
def api_bulk_update_tasks_list():
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
def filtered_view(view_name):
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

    return render_template(
        "filtered.html",
        tasks=filtered_tasks,
        view_name=view_name.title(),
        count=len(filtered_tasks),
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


@app.route("/syllabi/<course_code>")
def view_syllabus(course_code: str):
    """Serve generated syllabus for a course."""
    from flask import abort, send_from_directory

    # Use configured paths
    syllabi_dir = Config.SYLLABI_DIR

    # Try HTML first, then Markdown
    html_path = syllabi_dir / f"{course_code}.html"
    md_path = syllabi_dir / f"{course_code}.md"

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
        abort(404, f"Syllabus not found for {course_code}")


@app.template_filter("status_icon")
def status_icon(status: str) -> str:
    """Get icon for status."""
    icons = {"blocked": "🚫", "todo": "📋", "doing": "⚡", "review": "👀", "done": "✅"}
    return icons.get(status, "❓")


if __name__ == "__main__":
    port = int(os.environ.get("DASH_PORT", 5055))
    host = os.environ.get("DASH_HOST", "127.0.0.1")
    debug_mode = os.environ.get("FLASK_ENV", "development") == "development"
    app.run(host=host, port=port, debug=debug_mode)
