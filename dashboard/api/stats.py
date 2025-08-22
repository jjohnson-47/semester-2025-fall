#!/usr/bin/env python3
"""
Statistics API endpoints.
"""

from flask import jsonify

from dashboard.api import api_bp
from dashboard.services.task_service import TaskService


@api_bp.route("/stats", methods=["GET"])
def get_stats():
    """Get dashboard statistics."""
    data = TaskService._load_tasks_data()
    tasks = data.get("tasks", [])

    # Calculate statistics
    total = len(tasks)
    by_status = {}
    by_priority = {}
    by_course = {}

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
    completed = by_status.get("completed", 0)
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
def get_course_stats(course_code):
    """Get statistics for a specific course."""
    data = TaskService._load_tasks_data()
    tasks = [t for t in data.get("tasks", []) if t.get("course") == course_code.upper()]

    if not tasks:
        return jsonify({"error": "No tasks found for this course"}), 404

    # Calculate course-specific stats
    total = len(tasks)
    by_status = {}
    by_priority = {}
    by_category = {}

    for task in tasks:
        status = task.get("status", "unknown")
        by_status[status] = by_status.get(status, 0) + 1

        priority = task.get("priority", "unknown")
        by_priority[priority] = by_priority.get(priority, 0) + 1

        category = task.get("category", "uncategorized")
        by_category[category] = by_category.get(category, 0) + 1

    completed = by_status.get("completed", 0)
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
