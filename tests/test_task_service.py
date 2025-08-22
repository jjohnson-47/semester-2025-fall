#!/usr/bin/env python3
"""
Unit tests for TaskService to exercise file I/O, filtering, and bulk ops.
"""

from __future__ import annotations

import pytest

from dashboard import create_app
from dashboard.services.task_service import TaskService


@pytest.fixture
def app():
    app = create_app("testing")
    app.config["TESTING"] = True
    return app


def test_task_service_crud_and_bulk(app):
    with app.app_context():
        # initialize_data should create file structure if missing
        TaskService.initialize_data()

        # Create
        t1 = TaskService.create_task(
            {
                "course": "MATH221",
                "title": "Seed",
                "status": "todo",
                "priority": "medium",
                "category": "setup",
            }
        )
        assert t1["id"]

        # Read by id
        got = TaskService.get_task_by_id(t1["id"])
        assert got and got["title"] == "Seed"

        # Update
        updated = TaskService.update_task(t1["id"], {"title": "Updated"})
        assert updated and updated["title"] == "Updated"

        # Status update
        assert TaskService.update_task_status(t1["id"], "in_progress") is True
        assert TaskService.get_task_by_id(t1["id"])["status"] == "in_progress"

        # Bulk add more
        TaskService.create_task(
            {
                "id": "BULK-1",
                "course": "MATH221",
                "title": "B1",
                "status": "todo",
                "priority": "high",
                "category": "setup",
            }
        )
        TaskService.create_task(
            {
                "id": "BULK-2",
                "course": "MATH221",
                "title": "B2",
                "status": "todo",
                "priority": "high",
                "category": "setup",
            }
        )

        # Get tasks with filtering + pagination
        page1 = TaskService.get_tasks(course="MATH221", page=1, per_page=2)
        assert page1["page"] == 1 and page1["per_page"] == 2
        assert page1["total"] >= 3

        # Bulk update
        count = TaskService.bulk_update(
            {"course": "MATH221", "status": "todo"}, {"status": "completed"}
        )
        assert count >= 2

        # Delete task
        assert TaskService.delete_task("BULK-1") is True
        assert TaskService.get_task_by_id("BULK-1") is None

        # Reset all to todo
        TaskService.reset_all_tasks()
        all_after_reset = TaskService.get_tasks()["tasks"]
        assert all(t["status"] == "todo" for t in all_after_reset)

        # Seed sample data and verify it adds some tasks
        before = TaskService.get_tasks()["total"]
        TaskService.seed_sample_data()
        after = TaskService.get_tasks()["total"]
        assert after > before
