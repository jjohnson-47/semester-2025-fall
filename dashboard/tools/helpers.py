#!/usr/bin/env python3
"""
Shared helper functions for dashboard tools.
"""

import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


def generate_task_id() -> str:
    """Generate a unique task ID."""
    return f"task-{uuid.uuid4().hex[:8]}"


def calculate_due_date(
    start_date: datetime, days_before: int | None = None, days_after: int | None = None
) -> datetime:
    """Calculate due date relative to start date."""
    if days_before:
        return start_date - timedelta(days=days_before)
    elif days_after:
        return start_date + timedelta(days=days_after)
    return start_date


def format_date_for_display(date: datetime, fmt: str = "%b %d, %Y") -> str:
    """Format date for display."""
    return date.strftime(fmt)


def priority_sort_key(task: dict[str, Any]) -> int:
    """Return sort key for priority-based sorting."""
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "none": 4}
    return priority_order.get(task.get("priority", "none"), 4)


def validate_task_structure(task: dict[str, Any]) -> bool:
    """Validate that a task has required fields."""
    required_fields = ["id", "course", "title", "status", "priority", "category"]
    return all(field in task for field in required_fields)


def validate_dates(tasks: list) -> list:
    """Validate date formats in tasks."""
    errors = []
    for task in tasks:
        if "due_date" in task:
            try:
                datetime.fromisoformat(task["due_date"])
            except (ValueError, TypeError):
                errors.append(
                    f"Task {task.get('id', 'unknown')}: Invalid date format '{task['due_date']}'"
                )
    return errors


def check_duplicates(tasks: list) -> list:
    """Check for duplicate task IDs."""
    seen_ids = set()
    duplicates = []

    for task in tasks:
        task_id = task.get("id")
        if task_id in seen_ids:
            duplicates.append(task_id)
        seen_ids.add(task_id)

    return duplicates


def validate_dependencies(tasks: list) -> list:
    """Validate task dependencies exist."""
    errors = []
    task_ids = {task.get("id") for task in tasks}

    for task in tasks:
        if "depends_on" in task:
            for dep_id in task["depends_on"]:
                if dep_id not in task_ids:
                    errors.append(f"Task {task.get('id')}: Missing dependency '{dep_id}'")

    return errors


def load_templates(template_file: str | Path) -> list[Any]:
    """Load task templates from file."""
    import json

    with open(template_file) as f:
        data = json.load(f)
    templates = data.get("templates", [])
    return list(templates) if templates else []


def generate_task_from_template(
    template: dict[str, Any], course: dict[str, Any], start_date: datetime
) -> dict[str, Any]:
    """Generate a task from a template."""
    task = {
        "id": generate_task_id(),
        "course": course["code"],
        "title": template["title"].format(course=course["code"]),
        "category": template["category"],
        "priority": template["priority"],
        "status": "todo",
        "description": template.get("description", "").format(course=course["code"]),
    }

    # Calculate due date
    if "days_before_start" in template:
        due_date = calculate_due_date(start_date, days_before=template["days_before_start"])
        task["due_date"] = due_date.strftime("%Y-%m-%d")

    return task


def generate_all_tasks(courses: list, templates: list, start_date: datetime) -> list:
    """Generate tasks for all courses from templates."""
    tasks = []
    for course in courses:
        for template in templates:
            task = generate_task_from_template(template, course, start_date)
            tasks.append(task)
    return tasks


def main() -> int:
    """Placeholder main function for testing."""
    return 0


def validate_all(tasks_file: str | Path) -> dict[str, Any]:
    """Validate all aspects of task data."""
    import json

    with open(tasks_file) as f:
        data = json.load(f)

    tasks = data.get("tasks", [])
    errors = []

    # Check structure
    for task in tasks:
        if not validate_task_structure(task):
            errors.append(f"Task {task.get('id', 'unknown')}: Invalid structure")

    # Check dates
    errors.extend(validate_dates(tasks))

    # Check duplicates
    duplicates = check_duplicates(tasks)
    if duplicates:
        errors.append(f"Duplicate IDs found: {', '.join(duplicates)}")

    # Check dependencies
    errors.extend(validate_dependencies(tasks))

    return {"valid": len(errors) == 0, "error_count": len(errors), "errors": errors}
