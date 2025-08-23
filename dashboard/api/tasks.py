#!/usr/bin/env python3
"""
Task API endpoints.
Handles CRUD operations for tasks.
"""

from flask import current_app, jsonify, request
from flask.typing import ResponseReturnValue

from dashboard.api import api_bp
from dashboard.services.task_service import TaskService
from dashboard.utils.decorators import validate_json


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
def get_task(task_id: str) -> ResponseReturnValue:
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
        data = request.get_json()

        # Validate required fields
        if not data.get("title") or not data.get("course"):
            return jsonify({"error": "Title and course are required"}), 400

        # Create task
        task = TaskService.create_task(data)
        return jsonify(task), 201

    except Exception as e:
        current_app.logger.error(f"Error creating task: {e}")
        return jsonify({"error": "Failed to create task"}), 500


@api_bp.route("/tasks/<task_id>", methods=["PUT"])
@validate_json
def update_task(task_id: str) -> ResponseReturnValue:
    """Update an existing task."""
    try:
        data = request.get_json()

        task = TaskService.update_task(task_id, data)
        if not task:
            return jsonify({"error": "Task not found"}), 404

        return jsonify({"success": True, "task": task})

    except Exception as e:
        current_app.logger.error(f"Error updating task {task_id}: {e}")
        return jsonify({"error": "Failed to update task"}), 500


@api_bp.route("/tasks/<task_id>", methods=["DELETE"])
def delete_task(task_id: str) -> ResponseReturnValue:
    """Delete a task."""
    try:
        success = TaskService.delete_task(task_id)
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

        # Validate status value
        valid_statuses = ["blocked", "todo", "in_progress", "done", "completed"]
        if status not in valid_statuses:
            return (
                jsonify({"error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}),
                400,
            )

        success = TaskService.update_task_status(task_id, status)
        if not success:
            return jsonify({"error": "Task not found"}), 404

        return jsonify({"success": True})

    except Exception as e:
        current_app.logger.error(f"Error updating task status: {e}")
        return jsonify({"error": "Failed to update status"}), 500


@api_bp.route("/tasks/bulk", methods=["GET"])
def get_bulk_tasks() -> ResponseReturnValue:
    """Get all tasks without pagination."""
    try:
        # Get all tasks without filters or pagination
        data = TaskService._load_tasks_data()
        tasks = data.get("tasks", [])
        return jsonify({"tasks": tasks, "total": len(tasks)})

    except Exception as e:
        current_app.logger.error(f"Error getting bulk tasks: {e}")
        return jsonify({"error": "Failed to retrieve tasks"}), 500


@api_bp.route("/tasks/reset", methods=["POST"])
def reset_tasks() -> ResponseReturnValue:
    """Reset all tasks to TODO status."""
    try:
        TaskService.reset_all_tasks()
        return jsonify({"success": True, "message": "All tasks reset to TODO"})

    except Exception as e:
        current_app.logger.error(f"Error resetting tasks: {e}")
        return jsonify({"error": "Failed to reset tasks"}), 500
