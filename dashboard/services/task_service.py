#!/usr/bin/env python3
"""
Task service for managing task operations.
"""

import fcntl
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from flask import current_app


class TaskService:
    """Service for task management operations."""

    @staticmethod
    def _get_tasks_file() -> Path:
        """Get the tasks file path from config."""
        return current_app.config["TASKS_FILE"]

    @staticmethod
    def _load_tasks_data() -> dict[str, Any]:
        """Load tasks from file with locking."""
        tasks_file = TaskService._get_tasks_file()

        if not tasks_file.exists():
            return {
                "tasks": [],
                "metadata": {"version": "1.0", "updated": datetime.now().isoformat()},
            }

        with open(tasks_file) as f:
            fcntl.flock(f, fcntl.LOCK_SH)
            try:
                data = json.load(f)
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)

        return data

    @staticmethod
    def _save_tasks_data(data: dict[str, Any]) -> None:
        """Save tasks to file with locking."""
        tasks_file = TaskService._get_tasks_file()
        data["metadata"]["updated"] = datetime.now().isoformat()

        # Ensure directory exists
        tasks_file.parent.mkdir(parents=True, exist_ok=True)

        with open(tasks_file, "w") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                json.dump(data, f, indent=2)
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)

    @staticmethod
    def get_tasks(
        course: str | None = None,
        status: str | None = None,
        priority: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        """
        Get filtered and paginated tasks.

        Args:
            course: Filter by course code
            status: Filter by status
            priority: Filter by priority
            page: Page number
            per_page: Items per page

        Returns:
            Dictionary with tasks and metadata
        """
        data = TaskService._load_tasks_data()
        tasks = data.get("tasks", [])

        # Apply filters
        if course:
            tasks = [t for t in tasks if t.get("course") == course]
        if status:
            tasks = [t for t in tasks if t.get("status") == status]
        if priority:
            tasks = [t for t in tasks if t.get("priority") == priority]

        # Calculate pagination
        total = len(tasks)
        start = (page - 1) * per_page
        end = start + per_page

        return {
            "tasks": tasks[start:end],
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page,
        }

    @staticmethod
    def get_task_by_id(task_id: str) -> dict[str, Any] | None:
        """Get a specific task by ID."""
        data = TaskService._load_tasks_data()
        for task in data.get("tasks", []):
            if task.get("id") == task_id:
                return task
        return None

    @staticmethod
    def create_task(task_data: dict[str, Any]) -> dict[str, Any]:
        """
        Create a new task.

        Args:
            task_data: Task information

        Returns:
            Created task with ID
        """
        # Generate ID if not provided
        if "id" not in task_data:
            task_data["id"] = f"task-{uuid.uuid4().hex[:8]}"

        # Set defaults
        task_data.setdefault("created_at", datetime.now().isoformat())
        task_data.setdefault("updated_at", datetime.now().isoformat())

        # Load, add, and save
        data = TaskService._load_tasks_data()
        data["tasks"].append(task_data)
        TaskService._save_tasks_data(data)

        return task_data

    @staticmethod
    def update_task(task_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
        """
        Update an existing task.

        Args:
            task_id: Task ID to update
            updates: Fields to update

        Returns:
            Updated task or None if not found
        """
        data = TaskService._load_tasks_data()

        for task in data.get("tasks", []):
            if task.get("id") == task_id:
                task.update(updates)
                task["updated_at"] = datetime.now().isoformat()
                TaskService._save_tasks_data(data)
                return task

        return None

    @staticmethod
    def update_task_status(task_id: str, status: str) -> bool:
        """
        Update task status.

        Args:
            task_id: Task ID
            status: New status

        Returns:
            True if successful, False if task not found
        """
        return TaskService.update_task(task_id, {"status": status}) is not None

    @staticmethod
    def delete_task(task_id: str) -> bool:
        """
        Delete a task.

        Args:
            task_id: Task ID to delete

        Returns:
            True if deleted, False if not found
        """
        data = TaskService._load_tasks_data()
        original_count = len(data.get("tasks", []))

        data["tasks"] = [t for t in data.get("tasks", []) if t.get("id") != task_id]

        if len(data["tasks"]) < original_count:
            TaskService._save_tasks_data(data)
            return True

        return False

    @staticmethod
    def bulk_update(filter_params: dict[str, Any], updates: dict[str, Any]) -> int:
        """
        Bulk update tasks matching filter.

        Args:
            filter_params: Fields to match
            updates: Fields to update

        Returns:
            Number of tasks updated
        """
        data = TaskService._load_tasks_data()
        updated_count = 0

        for task in data.get("tasks", []):
            # Check if task matches all filter params
            matches = all(task.get(key) == value for key, value in filter_params.items())

            if matches:
                task.update(updates)
                task["updated_at"] = datetime.now().isoformat()
                updated_count += 1

        if updated_count > 0:
            TaskService._save_tasks_data(data)

        return updated_count

    @staticmethod
    def initialize_data() -> None:
        """Initialize empty task data file."""
        tasks_file = TaskService._get_tasks_file()
        if not tasks_file.exists():
            initial_data = {
                "tasks": [],
                "metadata": {
                    "version": "1.0",
                    "created": datetime.now().isoformat(),
                    "updated": datetime.now().isoformat(),
                },
            }
            TaskService._save_tasks_data(initial_data)

    @staticmethod
    def seed_sample_data() -> None:
        """Seed database with sample tasks."""
        sample_tasks = [
            {
                "id": f"task-{uuid.uuid4().hex[:8]}",
                "course": "MATH221",
                "title": "Prepare syllabus",
                "status": "completed",
                "priority": "high",
                "category": "setup",
                "due_date": "2025-08-15",
                "description": "Finalize and upload syllabus to Blackboard",
            },
            {
                "id": f"task-{uuid.uuid4().hex[:8]}",
                "course": "MATH251",
                "title": "Setup Blackboard shell",
                "status": "in_progress",
                "priority": "high",
                "category": "technical",
                "due_date": "2025-08-20",
                "description": "Configure course modules and assignments",
            },
            {
                "id": f"task-{uuid.uuid4().hex[:8]}",
                "course": "STAT253",
                "title": "Order textbooks",
                "status": "todo",
                "priority": "critical",
                "category": "materials",
                "due_date": "2025-08-10",
                "description": "Ensure bookstore has sufficient copies",
            },
        ]

        for task in sample_tasks:
            task["created_at"] = datetime.now().isoformat()
            task["updated_at"] = datetime.now().isoformat()

        data = TaskService._load_tasks_data()
        data["tasks"].extend(sample_tasks)
        TaskService._save_tasks_data(data)

    @staticmethod
    def reset_all_tasks() -> None:
        """Reset all tasks to 'todo' status."""
        data = TaskService._load_tasks_data()

        for task in data.get("tasks", []):
            task["status"] = "todo"
            task["updated_at"] = datetime.now().isoformat()

        TaskService._save_tasks_data(data)
