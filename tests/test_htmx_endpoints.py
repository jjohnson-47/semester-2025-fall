#!/usr/bin/env python3
"""
Tests for HTMX-specific endpoints with out-of-band swap validation.

These tests ensure that:
- HTMX endpoints return proper HTML fragments
- Out-of-band swaps are correctly formatted
- Dependency updates trigger appropriate OOB updates
- Response headers are correct for HTMX

Following Flask testing best practices from Flask 3.x documentation.
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent.parent))

from dashboard import create_app
from dashboard.services.dependency_service import DependencyService


class TestHTMXEndpoints:
    """Test suite for HTMX-powered endpoints."""

    @pytest.fixture
    def app(self):
        """Create Flask app in testing configuration."""
        app = create_app("testing")
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()

    @pytest.fixture
    def mock_dependency_service(self):
        """Mock DependencyService for isolated testing."""
        with patch("dashboard.api.tasks_htmx.DependencyService") as mock:
            yield mock

    def test_update_task_status_returns_html_fragment(self, client, mock_dependency_service):
        """Test that status update returns HTML fragment, not JSON."""
        mock_dependency_service.update_task_status.return_value = {
            "updated_task": {
                "id": "TEST-001",
                "title": "Test Task",
                "course": "TEST",
                "status": "done",
                "priority": "high",
                "category": "setup",
                "is_blocked": False,
                "depends_on": [],
                "children": [],
            },
            "affected_tasks": [],
        }

        response = client.post("/api/tasks/TEST-001/status", data={"status": "done"})

        assert response.status_code == 200
        assert response.content_type == "text/html; charset=utf-8"

        # Parse HTML to verify it's a valid fragment
        soup = BeautifulSoup(response.data, "html.parser")
        task_row = soup.find("tr", id="task-TEST-001")
        assert task_row is not None

    def test_update_task_status_with_oob_swaps(self, client, mock_dependency_service):
        """Test that completing a task returns OOB swaps for unblocked tasks."""
        mock_dependency_service.update_task_status.return_value = {
            "updated_task": {
                "id": "BLOCKER-001",
                "title": "Blocking Task",
                "course": "TEST",
                "status": "done",
                "priority": "high",
                "category": "setup",
                "is_blocked": False,
                "depends_on": [],
                "children": [],
            },
            "affected_tasks": [
                {
                    "id": "UNBLOCKED-001",
                    "title": "Now Unblocked",
                    "course": "TEST",
                    "status": "todo",
                    "priority": "medium",
                    "category": "content",
                    "is_blocked": False,
                    "depends_on": ["BLOCKER-001"],
                    "children": [],
                },
                {
                    "id": "UNBLOCKED-002",
                    "title": "Also Unblocked",
                    "course": "TEST",
                    "status": "todo",
                    "priority": "low",
                    "category": "setup",
                    "is_blocked": False,
                    "depends_on": ["BLOCKER-001"],
                    "children": [],
                },
            ],
            "affected_count": 2,
        }

        response = client.post("/api/tasks/BLOCKER-001/status", data={"status": "done"})

        assert response.status_code == 200

        # Parse response for OOB swaps
        html = response.data.decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")

        # Find elements with hx-swap-oob attribute
        oob_elements = soup.find_all(attrs={"hx-swap-oob": "true"})
        assert len(oob_elements) >= 2  # At least the 2 unblocked tasks

        # Verify the OOB elements have correct IDs
        oob_ids = [elem.get("id") for elem in oob_elements if elem.get("id")]
        assert "task-UNBLOCKED-001" in oob_ids
        assert "task-UNBLOCKED-002" in oob_ids

    def test_quick_complete_task(self, client, mock_dependency_service):
        """Test quick task completion endpoint."""
        mock_dependency_service.complete_task.return_value = {
            "completed_task": {
                "id": "QUICK-001",
                "title": "Quick Task",
                "course": "TEST",
                "status": "done",
                "priority": "high",
                "category": "setup",
                "is_blocked": False,
                "depends_on": [],
                "children": [],
            },
            "unblocked_tasks": [
                {
                    "id": "NEXT-001",
                    "title": "Next Task",
                    "course": "TEST",
                    "status": "todo",
                    "priority": "medium",
                    "category": "content",
                    "is_blocked": False,
                    "depends_on": ["QUICK-001"],
                    "children": [],
                }
            ],
            "unblocked_count": 1,
        }

        response = client.post("/api/tasks/QUICK-001/complete")

        assert response.status_code == 200

        # Verify notification is included
        html = response.data.decode("utf-8")
        assert "🎉" in html  # Celebration emoji for unblocked tasks
        assert "1 task(s) unblocked" in html

    def test_get_task_children_lazy_loading(self, client, mock_dependency_service):
        """Test lazy loading of child tasks."""
        mock_dependency_service.get_task_hierarchy.return_value = {
            "children_map": {"PARENT-001": ["CHILD-001", "CHILD-002"]},
            "task_map": {
                "CHILD-001": {
                    "id": "CHILD-001",
                    "title": "Child Task 1",
                    "course": "TEST",
                    "status": "todo",
                    "priority": "medium",
                    "category": "setup",
                    "parent_id": "PARENT-001",
                    "is_blocked": False,
                    "depends_on": [],
                    "children": [],
                },
                "CHILD-002": {
                    "id": "CHILD-002",
                    "title": "Child Task 2",
                    "course": "TEST",
                    "status": "todo",
                    "priority": "low",
                    "category": "content",
                    "parent_id": "PARENT-001",
                    "is_blocked": False,
                    "depends_on": [],
                    "children": [],
                },
            },
        }

        response = client.get("/api/tasks/PARENT-001/children")

        assert response.status_code == 200

        soup = BeautifulSoup(response.data, "html.parser")

        # Should return child task rows
        child_rows = soup.find_all("tr", class_="task-child")
        assert len(child_rows) >= 2

    def test_kanban_view_html_structure(self, client, mock_dependency_service):
        """Test that Kanban view returns proper HTML structure."""
        mock_dependency_service.get_task_hierarchy.return_value = {
            "task_map": {
                "BLOCKED-001": {
                    "id": "BLOCKED-001",
                    "title": "Blocked Task",
                    "course": "TEST",
                    "status": "blocked",
                    "priority": "high",
                    "category": "setup",
                    "is_blocked": True,
                    "depends_on": ["MISSING"],
                    "children": [],
                    "blocker_titles": ["Missing Task"],
                },
                "TODO-001": {
                    "id": "TODO-001",
                    "title": "Todo Task",
                    "course": "TEST",
                    "status": "todo",
                    "priority": "medium",
                    "category": "content",
                    "is_blocked": False,
                    "depends_on": [],
                    "children": [],
                },
            }
        }

        response = client.get("/api/tasks/kanban")

        assert response.status_code == 200

        soup = BeautifulSoup(response.data, "html.parser")

        # Should have 4 columns
        columns = soup.find_all(class_="kanban-column")
        assert len(columns) == 4

        # Should have draggable cards
        cards = soup.find_all(class_="kanban-card")
        assert len(cards) >= 2

        # Cards should have data attributes for drag/drop
        for card in cards:
            assert card.get("data-task-id") is not None

    def test_quick_add_task_from_command_palette(self, client):
        """Test quick task addition from command palette."""
        with patch("dashboard.api.tasks_htmx.TaskService") as mock_task_service:
            mock_task_service.create_task.return_value = {
                "id": "NEW-001",
                "course": "MATH221",
                "title": "New Quick Task",
                "status": "todo",
                "priority": "medium",
                "category": "setup",
            }

            with patch.object(DependencyService, "get_task_hierarchy") as mock_hierarchy:
                mock_hierarchy.return_value = {
                    "root_tasks": [
                        {
                            "id": "NEW-001",
                            "title": "New Quick Task",
                            "course": "MATH221",
                            "status": "todo",
                            "priority": "medium",
                            "category": "setup",
                            "is_blocked": False,
                            "depends_on": [],
                            "children": [],
                        }
                    ]
                }

                response = client.post(
                    "/api/tasks/quick-add", data={"title": "MATH221 New Quick Task"}
                )

                assert response.status_code == 200

                # Verify task was created with parsed course
                mock_task_service.create_task.assert_called_once()
                call_args = mock_task_service.create_task.call_args[0][0]
                assert call_args["course"] == "MATH221"
                assert call_args["title"] == "New Quick Task"

    def test_filtered_tasks_with_special_filters(self, client, mock_dependency_service):
        """Test special filters like 'overdue' and 'critical-path'."""
        from datetime import date, timedelta

        yesterday = (date.today() - timedelta(days=1)).isoformat()
        tomorrow = (date.today() + timedelta(days=1)).isoformat()

        mock_dependency_service.get_task_hierarchy.return_value = {
            "task_map": {
                "OVERDUE-001": {
                    "id": "OVERDUE-001",
                    "title": "Overdue Task",
                    "course": "TEST",
                    "status": "todo",
                    "priority": "high",
                    "category": "setup",
                    "due_date": yesterday,
                    "is_blocked": False,
                    "depends_on": [],
                    "children": [],
                },
                "FUTURE-001": {
                    "id": "FUTURE-001",
                    "title": "Future Task",
                    "course": "TEST",
                    "status": "todo",
                    "priority": "low",
                    "category": "content",
                    "due_date": tomorrow,
                    "is_blocked": False,
                    "depends_on": [],
                    "children": [],
                },
            }
        }

        response = client.get("/api/tasks/filtered?filter=overdue")

        assert response.status_code == 200

        soup = BeautifulSoup(response.data, "html.parser")
        task_rows = soup.find_all("tr", class_="task-row")

        # Should only show overdue task
        task_ids = [row.get("id") for row in task_rows]
        assert "task-OVERDUE-001" in task_ids
        assert "task-FUTURE-001" not in task_ids

    def test_htmx_headers_preserved(self, client, mock_dependency_service):
        """Test that HTMX-specific headers are handled correctly."""
        mock_dependency_service.update_task_status.return_value = {
            "updated_task": {
                "id": "TEST-001",
                "title": "Test Task",
                "course": "TEST",
                "status": "done",
                "priority": "high",
                "category": "setup",
                "is_blocked": False,
                "depends_on": [],
                "children": [],
            },
            "affected_tasks": [],
        }

        # Simulate HTMX request with HX-Request header
        response = client.post(
            "/api/tasks/TEST-001/status",
            data={"status": "done"},
            headers={
                "HX-Request": "true",
                "HX-Trigger": "status-select",
                "HX-Target": "task-TEST-001",
            },
        )

        assert response.status_code == 200

        # Response should be HTML fragment for HTMX
        assert "application/json" not in response.content_type
        assert "text/html" in response.content_type

    @pytest.mark.parametrize(
        "status,should_be_disabled",
        [
            ("blocked", True),
            ("todo", False),
            ("in_progress", False),
            ("done", False),
        ],
    )
    def test_task_row_status_dropdown_state(
        self, client, mock_dependency_service, status, should_be_disabled
    ):
        """Test that status dropdown is disabled for blocked tasks."""
        mock_dependency_service.get_task_hierarchy.return_value = {
            "root_tasks": [
                {
                    "id": "TEST-001",
                    "title": "Test Task",
                    "course": "TEST",
                    "status": status,
                    "priority": "medium",
                    "category": "setup",
                    "is_blocked": status == "blocked",
                    "depends_on": ["DEPENDENCY"] if status == "blocked" else [],
                    "children": [],
                    "blocker_titles": ["Dependency Task"] if status == "blocked" else [],
                }
            ]
        }

        response = client.get("/api/tasks/list")
        soup = BeautifulSoup(response.data, "html.parser")

        status_select = soup.find("select", {"name": "status"})
        assert status_select is not None

        if should_be_disabled:
            assert status_select.get("disabled") is not None
        else:
            assert status_select.get("disabled") is None
