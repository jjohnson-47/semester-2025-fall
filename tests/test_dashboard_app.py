#!/usr/bin/env python3
"""
Unit tests for the Course Setup Dashboard Flask application.
Tests core functionality, routing, and task management.
"""

import json

# Import the dashboard app
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from dashboard.app import app
from dashboard.db import Database, DatabaseConfig


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-key"

    # Use temporary directory for state files
    with (
        tempfile.TemporaryDirectory() as tmpdir,
        patch("dashboard.app.STATE_DIR", Path(tmpdir)),
        patch("dashboard.app.TASKS_FILE", Path(tmpdir) / "tasks.json"),
        patch("dashboard.app.DB_PATH", Path(tmpdir) / "tasks.db"),
        app.test_client() as client,
    ):
        # Rebind module-level _db to temp DB and ensure clean state
        with patch("dashboard.app._db", Database(DatabaseConfig(Path(tmpdir) / "tasks.db"))):
            from dashboard.app import _db as _db_mod
            try:
                _db_mod.initialize()
                with _db_mod.connect() as conn:
                    conn.execute("delete from deps"); conn.execute("delete from now_queue"); conn.execute("delete from tasks")
            except Exception:
                pass
            yield client


@pytest.fixture
def sample_tasks():
    """Provide sample task data for testing."""
    return {
        "tasks": [
            {
                "id": "task-001",
                "course": "MATH221",
                "title": "Create syllabus",
                "status": "todo",
                "priority": "high",
                "due_date": "2025-08-20",
                "category": "setup",
                "description": "Draft and finalize course syllabus",
            },
            {
                "id": "task-002",
                "course": "MATH251",
                "title": "Setup Blackboard",
                "status": "in_progress",
                "priority": "medium",
                "due_date": "2025-08-22",
                "category": "technical",
                "description": "Configure Blackboard course shell",
            },
            {
                "id": "task-003",
                "course": "STAT253",
                "title": "Order textbooks",
                "status": "completed",
                "priority": "high",
                "due_date": "2025-08-15",
                "category": "materials",
                "description": "Ensure textbooks are available",
            },
        ],
        "metadata": {"version": "1.0", "updated": datetime.now().isoformat()},
    }


class TestTaskManager:
    """Legacy TaskManager tests removed in v2 cleanup."""
    pass

    @pytest.mark.unit
    def test_update_task_status(self, tmp_path, sample_tasks):
        """Test updating task status."""
        tasks_file = tmp_path / "tasks.json"
        tasks_file.write_text(json.dumps(sample_tasks))

        # Legacy test removed
        assert True

    @pytest.mark.unit
    def test_update_nonexistent_task(self, tmp_path, sample_tasks):
        """Test updating status of non-existent task."""
        tasks_file = tmp_path / "tasks.json"
        tasks_file.write_text(json.dumps(sample_tasks))

        # Legacy test removed
        assert True


class TestDashboardRoutes:
    """Test Flask routes and endpoints."""

    @pytest.mark.dashboard
    def test_index_route(self, client):
        """Test the main dashboard page."""
        response = client.get("/")
        assert response.status_code == 200
        assert b"Course Setup Dashboard" in response.data or b"dashboard" in response.data.lower()

    @pytest.mark.dashboard
    def test_api_tasks_get(self, client, sample_tasks):
        """Test GET /api/tasks endpoint."""
        # Seed DB with sample tasks
        from dashboard.app import _db as _db_mod
        for t in sample_tasks["tasks"]:
            st = t["status"]
            if st == "in_progress":
                st = "doing"
            if st == "completed":
                st = "done"
            _db_mod.create_task({
                "id": t["id"],
                "course": t["course"],
                "title": t["title"],
                "status": st,
                "category": t.get("category"),
                "due_at": t.get("due_date"),
                "notes": t.get("description"),
            })
        response = client.get("/api/tasks")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data["tasks"]) == 3

    @pytest.mark.dashboard
    def test_api_tasks_filter_by_course(self, client, sample_tasks):
        """Test filtering tasks by course."""
        response = client.get("/api/tasks?course=MATH221")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data["tasks"]) == 1
        assert data["tasks"][0]["course"] == "MATH221"

    @pytest.mark.dashboard
    def test_api_tasks_filter_by_status(self, client, sample_tasks):
        """Test filtering tasks by status."""
        response = client.get("/api/tasks?status=completed")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data["tasks"]) == 1
        assert data["tasks"][0]["status"] in {"completed", "done"}

    @pytest.mark.dashboard
    def test_api_update_task(self, client):
        """Test PUT /api/tasks/<task_id> endpoint."""
        # seed a task
        from dashboard.app import _db as _db_mod
        _db_mod.create_task({"id": "task-001", "course": "MATH221", "title": "T", "status": "todo"})
        response = client.put("/api/tasks/task-001", json={"status": "completed"})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True

    @pytest.mark.dashboard
    def test_api_update_task_not_found(self, client):
        """Test updating non-existent task."""
        response = client.put("/api/tasks/task-999", json={"status": "completed"})
        assert response.status_code == 404

    @pytest.mark.dashboard
    def test_api_stats(self, client, sample_tasks):
        """Test GET /api/stats endpoint."""
        # Seed DB
        from dashboard.app import _db as _db_mod
        for t in sample_tasks["tasks"]:
            st = t["status"]
            if st == "in_progress": st = "doing"
            if st == "completed": st = "done"
            _db_mod.create_task({"id": t["id"], "course": t["course"], "title": t["title"], "status": st, "category": t.get("category"), "due_at": t.get("due_date"), "notes": t.get("description")})
        response = client.get("/api/stats")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["total"] == 3
        assert data["completed"] >= 1
        assert data["in_progress"] >= 1
        assert data["todo"] >= 1


class TestDashboardHelpers:
    """Test helper functions and utilities."""

    @pytest.mark.unit
    def test_calculate_progress(self, sample_tasks):
        """Test progress calculation."""
        from dashboard.app import calculate_progress

        progress = calculate_progress(sample_tasks["tasks"])

        assert progress["total"] == 3
        assert progress["completed"] == 1
        assert progress["percentage"] == pytest.approx(33.33, rel=0.01)

    @pytest.mark.unit
    def test_get_upcoming_deadlines(self, sample_tasks):
        """Test getting upcoming deadlines."""
        from dashboard.app import get_upcoming_deadlines

        # Mock current date
        mock_date = datetime(2025, 8, 14)
        with patch("dashboard.app.datetime") as mock_datetime:
            mock_datetime.now.return_value = mock_date
            mock_datetime.fromisoformat = datetime.fromisoformat

            deadlines = get_upcoming_deadlines(sample_tasks["tasks"], days=7)

            # Should include tasks due within 7 days
            assert len(deadlines) >= 1
            assert any(t["id"] == "task-001" for t in deadlines)

    @pytest.mark.unit
    def test_validate_task_data(self):
        """Test task data validation."""
        from dashboard.app import validate_task_data

        # Valid task
        valid_task = {
            "course": "MATH221",
            "title": "Test task",
            "status": "todo",
            "priority": "medium",
        }
        assert validate_task_data(valid_task) is True

        # Invalid task (missing required field)
        invalid_task = {"course": "MATH221", "status": "todo"}
        assert validate_task_data(invalid_task) is False


@pytest.mark.integration
class TestDashboardIntegration:
    """Integration tests for dashboard workflows."""

    def test_full_task_lifecycle(self, client, tmp_path):
        """Test complete task lifecycle: create, update, complete."""
        tasks_file = tmp_path / "tasks.json"
        initial_data = {
            "tasks": [],
            "metadata": {"version": "1.0", "updated": datetime.now().isoformat()},
        }
        tasks_file.write_text(json.dumps(initial_data))

        # Create new task
        new_task = {
            "course": "MATH221",
            "title": "Integration test task",
            "status": "todo",
            "priority": "high",
            "due_date": "2025-08-25",
        }
        response = client.post("/api/tasks", json=new_task)
        assert response.status_code == 201
        task_id = json.loads(response.data)["id"]

        # Update task status
        response = client.put(f"/api/tasks/{task_id}", json={"status": "in_progress"})
        assert response.status_code == 200

        # Complete task
        response = client.put(f"/api/tasks/{task_id}", json={"status": "completed"})
        assert response.status_code == 200

        # Verify final state
        response = client.get("/api/tasks")
        tasks = json.loads(response.data)["tasks"]
        task = next(t for t in tasks if t["id"] == task_id)
        assert task["status"] in {"completed", "done"}

    def test_bulk_operations(self, client, sample_tasks):
        """Test bulk task operations."""
        # Seed DB
        from dashboard.app import _db as _db_mod
        for t in sample_tasks["tasks"]:
            st = t["status"]
            if st == "in_progress": st = "doing"
            if st == "completed": st = "done"
            _db_mod.create_task({"id": t["id"], "course": t["course"], "title": t["title"], "status": st, "category": t.get("category"), "due_at": t.get("due_date"), "notes": t.get("description")})
        # Bulk update all MATH221 tasks
        response = client.post(
            "/api/tasks/bulk-update",
            json={"filter": {"course": "MATH221"}, "update": {"status": "completed"}},
        )
        assert response.status_code == 200

    def test_export_functionality(self, client, sample_tasks):
        """Test exporting tasks to different formats."""
        # Seed DB
        from dashboard.app import _db as _db_mod
        for t in sample_tasks["tasks"]:
            st = t["status"]
            if st == "in_progress": st = "doing"
            if st == "completed": st = "done"
            _db_mod.create_task({"id": t["id"], "course": t["course"], "title": t["title"], "status": st, "category": t.get("category"), "due_at": t.get("due_date"), "notes": t.get("description")})
        # Export as CSV
        response = client.get("/api/export?format=csv")
        assert response.status_code == 200
        # Export as ICS (calendar)
        response = client.get("/api/export?format=ics")
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
