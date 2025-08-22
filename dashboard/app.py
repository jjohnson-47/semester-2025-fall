#!/usr/bin/env python3
"""
Course Setup Dashboard - Flask Application
Task management system for semester course preparation
"""

import fcntl
import json

# Set up logging
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytz
from flask import Flask, jsonify, render_template, request
from dashboard.config import Config

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)

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


@app.route("/")
def index():
    """Main dashboard view."""
    data = TaskManager.load_tasks()
    courses = TaskManager.load_courses()

    # Calculate priorities and add display helpers
    for task in data["tasks"]:
        task["priority"] = calculate_priority(task)
        task["status_color"] = get_status_color(task.get("status", "todo"))
        task["due_color"] = get_due_color(task)

        # Format due date for display
        if "due" in task:
            try:
                due = datetime.fromisoformat(task["due"])
                task["due_display"] = due.strftime("%b %d, %Y")
                task["due_relative"] = get_relative_time(due)
            except (ValueError, TypeError, AttributeError) as e:
                logger.debug(f"Failed to format due date for task {task.get('id')}: {e}")
                task["due_display"] = task["due"]

    # Sort by priority
    data["tasks"].sort(key=lambda t: t["priority"], reverse=True)

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
    )


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
def api_bulk_update():
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
    from dashboard.config import Config

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
    app.run(host=host, port=port, debug=True)
