#!/usr/bin/env python3
"""
Main web views for the dashboard.
"""

from flask import render_template

from dashboard.services.task_service import TaskService
from dashboard.views import main_bp


@main_bp.route("/")
def index() -> str:
    """Main dashboard page."""
    return render_template("dashboard.html")


@main_bp.route("/tasks")
def tasks_view() -> str:
    """Tasks list view."""
    tasks = TaskService.get_tasks()
    return render_template("tasks.html", tasks=tasks)


@main_bp.route("/courses")
def courses_view() -> str:
    """Courses overview."""
    return render_template("courses.html")
