#!/usr/bin/env python3
"""
Task API endpoints.
Handles CRUD operations for tasks.
"""

from flask import current_app, jsonify, request

from dashboard.api import api_bp
from dashboard.services.task_service import TaskService
from dashboard.utils.decorators import validate_json


@api_bp.route("/tasks", methods=["GET"])
def get_tasks():
    """
    Get list of tasks with optional filtering.

    Query parameters:
    - course: Filter by course code
    - status: Filter by task status
    - priority: Filter by priority level
    - page: Page number for pagination
    - per_page: Number of items per page
    """
    try:
        # Get query parameters
        course = request.args.get("course")
        status = request.args.get("status")
        priority = request.args.get("priority")
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 20))

        # Get filtered tasks
        tasks = TaskService.get_tasks(
            course=course, status=status, priority=priority, page=page, per_page=per_page
        )

        return jsonify(tasks)

    except Exception as e:
        current_app.logger.error(f"Error getting tasks: {e}")
        return jsonify({"error": "Failed to retrieve tasks"}), 500


@api_bp.route("/tasks/<task_id>", methods=["GET"])
def get_task(task_id):
    """Get a specific task by ID."""
    try:
        task = TaskService.get_task_by_id(task_id)
        if not task:
            return jsonify({"error": "Task not found"}), 404
        return jsonify(task)

    except Exception as e:
        current_app.logger.error(f"Error getting task {task_id}: {e}")
        return jsonify({"error": "Failed to retrieve task"}), 500


@api_bp.route("/tasks", methods=["POST"])
@validate_json
def create_task():
    """Create a new task."""
    try:
        data = request.get_json()

        # Validate required fields
        required = ["course", "title", "status", "priority"]
        missing = [field for field in required if field not in data]
        if missing:
            return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

        # Create task
        task = TaskService.create_task(data)
        return jsonify(task), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error creating task: {e}")
        return jsonify({"error": "Failed to create task"}), 500


@api_bp.route("/tasks/<task_id>", methods=["PUT"])
@validate_json
def update_task(task_id):
    """Update an existing task."""
    try:
        data = request.get_json()

        # Update task
        task = TaskService.update_task(task_id, data)
        if not task:
            return jsonify({"error": "Task not found"}), 404

        return jsonify({"success": True, "task": task})

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error updating task {task_id}: {e}")
        return jsonify({"error": "Failed to update task"}), 500


@api_bp.route("/tasks/<task_id>", methods=["DELETE"])
def delete_task(task_id):
    """Delete a task."""
    try:
        success = TaskService.delete_task(task_id)
        if not success:
            return jsonify({"error": "Task not found"}), 404

        return jsonify({"success": True, "message": "Task deleted"})

    except Exception as e:
        current_app.logger.error(f"Error deleting task {task_id}: {e}")
        return jsonify({"error": "Failed to delete task"}), 500


@api_bp.route("/tasks/bulk-update", methods=["POST"])
@validate_json
def bulk_update_tasks():
    """
    Bulk update multiple tasks.

    Request body:
    {
        "filter": {"course": "MATH221", "status": "todo"},
        "update": {"status": "in_progress"}
    }
    """
    try:
        data = request.get_json()

        if "filter" not in data or "update" not in data:
            return jsonify({"error": "Missing filter or update parameters"}), 400

        count = TaskService.bulk_update(data["filter"], data["update"])

        return jsonify({"success": True, "updated_count": count})

    except Exception as e:
        current_app.logger.error(f"Error in bulk update: {e}")
        return jsonify({"error": "Failed to perform bulk update"}), 500


@api_bp.route("/tasks/<task_id>/status", methods=["PATCH"])
@validate_json
def update_task_status(task_id):
    """Quick endpoint to update just the task status."""
    try:
        data = request.get_json()

        if "status" not in data:
            return jsonify({"error": "Status field required"}), 400

        valid_statuses = ["todo", "in_progress", "completed", "blocked", "deferred"]
        if data["status"] not in valid_statuses:
            return (
                jsonify({"error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}),
                400,
            )

        success = TaskService.update_task_status(task_id, data["status"])
        if not success:
            return jsonify({"error": "Task not found"}), 404

        return jsonify({"success": True, "status": data["status"]})

    except Exception as e:
        current_app.logger.error(f"Error updating task status: {e}")
        return jsonify({"error": "Failed to update status"}), 500
