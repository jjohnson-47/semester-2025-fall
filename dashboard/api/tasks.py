#!/usr/bin/env python3
"""
Task API endpoints (DB-backed).
Handles CRUD operations for tasks using the SQLite repository layer.
Includes status mapping for legacy values.
"""

import json
from pathlib import Path

from flask import current_app, jsonify, request
from flask.typing import ResponseReturnValue

from dashboard.api import api_bp
from dashboard.config import Config
from dashboard.db import Database, DatabaseConfig
from dashboard.utils.decorators import validate_json

# ------------------------------
# Helpers: DB and status mapping
# ------------------------------

_db = Database(DatabaseConfig(Config.STATE_DIR / "tasks.db"))
try:  # Initialize tables if needed (best-effort)
    _db.initialize()
except Exception as exc:
    current_app.logger.debug("DB init skipped in tasks API: %s", exc)


CANONICAL_STATUSES = {"todo", "doing", "review", "done", "blocked"}


def _map_incoming_status(value: str | None) -> str | None:
    if not value:
        return None
    v = value.strip().lower()
    # Legacy/alias mappings
    if v in {"in_progress", "in-progress", "progress"}:
        return "doing"
    if v in {"completed", "complete"}:
        return "done"
    if v in CANONICAL_STATUSES:
        return v
    return None


@api_bp.route("/tasks", methods=["GET"])
def get_tasks() -> ResponseReturnValue:
    """
    Get list of tasks with optional filtering.

    Query parameters:
    - course: Filter by course code
    - status: Filter by task status
    - priority: Filter by priority level
    - page: Page number for pagination
    - per_page: Number of items per page
    """
    # Query params (DB-backed)
    course = request.args.get("course")
    status = _map_incoming_status(request.args.get("status")) or request.args.get("status")
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))

    # Fetch from DB
    try:
        tasks = _db.list_tasks(status=status, course=course)
    except Exception as e:  # pragma: no cover - unexpected
        current_app.logger.error(f"DB error listing tasks: {e}")
        return jsonify({"error": "Failed to retrieve tasks"}), 500

    total = len(tasks)
    start = max(0, (page - 1) * per_page)
    end = start + per_page
    return jsonify(
        {
            "tasks": tasks[start:end],
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page,
        }
    )


@api_bp.route("/tasks/<task_id>", methods=["GET"])
def get_task(task_id: str) -> ResponseReturnValue:
    """Get a specific task by ID."""
    try:
        task = _db.get_task(task_id)
        if not task:
            return jsonify({"error": "Task not found"}), 404
        return jsonify(task)
    except Exception as e:
        current_app.logger.error(f"Error getting task {task_id}: {e}")
        return jsonify({"error": "Failed to retrieve task"}), 500


@api_bp.route("/tasks", methods=["POST"])
@validate_json
def create_task() -> ResponseReturnValue:
    """
    Create a new task.

    Expected JSON body:
    - title: Task title (required)
    - course: Course code (required)
    - description: Task description
    - priority: Priority level
    - due_date: Due date in ISO format
    - depends_on: List of prerequisite task IDs
    """
    try:
        data = request.get_json() or {}
        # Required
        if not data.get("title") or not data.get("course"):
            return jsonify({"error": "Title and course are required"}), 400
        # Status mapping
        mapped = _map_incoming_status(data.get("status")) or data.get("status") or "todo"
        if mapped not in CANONICAL_STATUSES:
            mapped = "todo"
        task_fields = {
            "id": data.get("id"),
            "course": data.get("course"),
            "title": data.get("title"),
            "status": mapped,
            "category": data.get("category"),
            "due_at": data.get("due_at") or data.get("due_date"),
            "est_minutes": data.get("est_minutes"),
            "notes": data.get("description") or data.get("notes"),
            "weight": data.get("weight", 1.0),
            "anchor": data.get("anchor"),
            "depends_on": data.get("depends_on"),
        }
        new_id = _db.create_task(task_fields)
        created = _db.get_task(new_id)
        return jsonify(created), 201
    except Exception as e:
        current_app.logger.error(f"Error creating task: {e}")
        return jsonify({"error": "Failed to create task"}), 500


@api_bp.route("/tasks/<task_id>", methods=["PUT"])
@validate_json
def update_task(task_id: str) -> ResponseReturnValue:
    """Update an existing task."""
    try:
        data = request.get_json() or {}
        # Map status if present
        if "status" in data:
            ms = _map_incoming_status(data.get("status"))
            if ms:
                data["status"] = ms
        # Filter to allowed fields
        allowed = {
            k: data[k]
            for k in ["status", "title", "due_at", "est_minutes", "weight", "category", "notes"]
            if k in data
        }
        if not allowed:
            # Nothing to update
            current = _db.get_task(task_id)
            if not current:
                return jsonify({"error": "Task not found"}), 404
            return jsonify({"success": True, "task": current})
        ok = _db.update_task_fields(task_id, allowed)
        if not ok:
            return jsonify({"error": "Task not found or no updatable fields"}), 404
        return jsonify({"success": True, "task": _db.get_task(task_id)})
    except Exception as e:
        current_app.logger.error(f"Error updating task {task_id}: {e}")
        return jsonify({"error": "Failed to update task"}), 500


@api_bp.route("/tasks/<task_id>", methods=["DELETE"])
def delete_task(task_id: str) -> ResponseReturnValue:
    """Delete a task."""
    try:
        success = _db.delete_task(task_id)
        if not success:
            return jsonify({"error": "Task not found"}), 404
        return jsonify({"success": True})
    except Exception as e:
        current_app.logger.error(f"Error deleting task {task_id}: {e}")
        return jsonify({"error": "Failed to delete task"}), 500


@api_bp.route("/tasks/<task_id>/status", methods=["PATCH"])
@validate_json
def update_task_status(task_id: str) -> ResponseReturnValue:
    """
    Update task status.

    Expected JSON body:
    - status: New status value
    """
    try:
        data = request.get_json()
        status = data.get("status")
        if not status:
            return jsonify({"error": "Status is required"}), 400
        mapped = _map_incoming_status(status)
        if not mapped:
            return jsonify({"error": "Invalid status"}), 400
        ok = _db.update_task_field(task_id, "status", mapped)
        if not ok:
            return jsonify({"error": "Task not found"}), 404
        return jsonify({"success": True})

    except Exception as e:
        current_app.logger.error(f"Error updating task status: {e}")
        return jsonify({"error": "Failed to update status"}), 500


@api_bp.route("/tasks/bulk", methods=["GET"])
def get_bulk_tasks() -> ResponseReturnValue:
    """Get all tasks without pagination."""
    # Testing fallback reads legacy JSON if present
    if current_app.config.get("TESTING") and not current_app.config.get("API_FORCE_DB"):
        try:
            p = Path(Config.STATE_DIR) / "tasks.json"
            if p.exists():
                data = json.loads(p.read_text())
                tasks = list(data.get("tasks", []))
                return jsonify({"tasks": tasks, "total": len(tasks)})
        except Exception:
            pass
    try:
        tasks = _db.list_tasks()
        return jsonify({"tasks": tasks, "total": len(tasks)})
    except Exception as e:
        current_app.logger.error(f"Error getting bulk tasks: {e}")
        return jsonify({"error": "Failed to retrieve tasks"}), 500


@api_bp.route("/tasks/reset", methods=["POST"])
def reset_tasks() -> ResponseReturnValue:
    """Reset all tasks to TODO status."""
    # Always use DB. In testing, read-only JSON fallback is not supported for reset.
    try:
        n = _db.reset_all_statuses("todo")
        return jsonify({"success": True, "message": f"All tasks reset to TODO ({n} updated)"})
    except Exception as e:
        current_app.logger.error(f"Error resetting tasks: {e}")
        return jsonify({"error": "Failed to reset tasks"}), 500
