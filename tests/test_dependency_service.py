#!/usr/bin/env python3
"""
Integration tests for the DependencyService.

Tests the complete dependency resolution system including:
- Task hierarchy building
- Dependency validation
- Auto-unlocking behavior
- Critical path calculation
- Error handling

Uses pytest fixtures for realistic test scenarios.
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from dashboard.models import Task, TaskStatus
from dashboard.services.dependency_service import DependencyService


class TestDependencyService:
    """Integration tests for dependency management service."""

    @pytest.fixture(autouse=True)
    def setup_test_environment(self, tmp_path):
        """Set up isolated test environment for each test."""
        # Create temporary state directory
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        db_path = state_dir / "tasks.db"

        # Force DB-backed behavior for testing
        # Patch the Database instance directly in the dependency_service module
        from dashboard.db import Database, DatabaseConfig
        test_db = Database(DatabaseConfig(db_path))
        test_db.initialize()
        
        with patch("dashboard.services.dependency_service.Config.API_FORCE_DB", True), \
             patch("dashboard.services.dependency_service.Config.STATE_DIR", state_dir), \
             patch("dashboard.services.dependency_service._db", test_db):
            yield test_db

    @pytest.fixture
    def sample_task_data(self) -> dict[str, Any]:
        """Create sample task data with dependencies."""
        return {
            "tasks": [
                {
                    "id": "MATH221-SYLLABUS",
                    "course": "MATH221",
                    "title": "Create syllabus",
                    "status": "todo",
                    "priority": "high",
                    "category": "setup",
                    "depends_on": [],
                    "parent_id": None,
                },
                {
                    "id": "MATH221-BB-SETUP",
                    "course": "MATH221",
                    "title": "Setup Blackboard",
                    "status": "blocked",
                    "priority": "high",
                    "category": "technical",
                    "depends_on": ["MATH221-SYLLABUS"],
                    "parent_id": None,
                },
                {
                    "id": "MATH221-BB-GRADEBOOK",
                    "course": "MATH221",
                    "title": "Configure gradebook",
                    "status": "blocked",
                    "priority": "medium",
                    "category": "technical",
                    "depends_on": ["MATH221-BB-SETUP"],
                    "parent_id": "MATH221-BB-SETUP",
                },
                {
                    "id": "MATH221-BB-ASSIGNMENT",
                    "course": "MATH221",
                    "title": "Create first assignment",
                    "status": "blocked",
                    "priority": "medium",
                    "category": "content",
                    "depends_on": ["MATH221-BB-GRADEBOOK"],
                    "parent_id": "MATH221-BB-SETUP",
                },
            ],
            "metadata": {"version": "2.0", "updated": datetime.now().isoformat()},
        }

    @pytest.fixture
    def populated_service(self, setup_test_environment, sample_task_data):
        """Create a DependencyService with sample data."""
        db = setup_test_environment

        # Insert tasks into database
        for task in sample_task_data.get("tasks", []):
            db.create_task(task)

        return DependencyService()

    def test_build_task_graph(self, populated_service):
        """Test building a complete task graph from stored data."""
        graph = populated_service.build_task_graph()

        assert len(graph.tasks) == 4
        assert "MATH221-SYLLABUS" in graph.tasks
        assert "MATH221-BB-ASSIGNMENT" in graph.tasks

        # Check relationships are preserved
        assignment = graph.get_task("MATH221-BB-ASSIGNMENT")
        assert assignment.depends_on == ["MATH221-BB-GRADEBOOK"]
        assert assignment.parent_id == "MATH221-BB-SETUP"

    def test_get_task_hierarchy(self, populated_service):
        """Test building hierarchical task structure."""
        hierarchy = populated_service.get_task_hierarchy()

        # Should have 2 root tasks (SYLLABUS and BB-SETUP)
        assert len(hierarchy["root_tasks"]) == 2

        # BB-SETUP should have children
        assert "MATH221-BB-SETUP" in hierarchy["children_map"]
        children_ids = hierarchy["children_map"]["MATH221-BB-SETUP"]
        assert "MATH221-BB-GRADEBOOK" in children_ids
        assert "MATH221-BB-ASSIGNMENT" in children_ids

        # Tasks should have blocker information
        assignment = hierarchy["task_map"]["MATH221-BB-ASSIGNMENT"]
        assert assignment["is_blocked"] is True
        assert "Configure gradebook" in assignment["blocker_titles"]

    def test_get_task_hierarchy_with_course_filter(self, populated_service):
        """Test filtering hierarchy by course."""
        # Add a task from different course
        graph = populated_service.build_task_graph()
        other_task = Task(id="MATH251-SYLLABUS", course="MATH251", title="Math 251 Syllabus")
        graph.add_task(other_task)
        populated_service._save_graph(graph)

        # Get hierarchy for MATH221 only
        hierarchy = populated_service.get_task_hierarchy(course="MATH221")

        # Should only include MATH221 tasks
        all_tasks = list(hierarchy["task_map"].keys())
        assert all("MATH221" in task_id for task_id in all_tasks)
        assert "MATH251-SYLLABUS" not in all_tasks

    def test_complete_task_with_cascading_unlock(self, populated_service):
        """Test completing a task and unlocking dependencies."""
        # Complete the first task
        result = populated_service.complete_task("MATH221-SYLLABUS")

        assert "error" not in result
        assert result["completed_task"]["status"] == "done"
        assert result["unblocked_count"] == 1
        assert len(result["unblocked_tasks"]) == 1
        assert result["unblocked_tasks"][0]["id"] == "MATH221-BB-SETUP"

        # Verify the unblocked task status was updated
        graph = populated_service.build_task_graph()
        bb_setup = graph.get_task("MATH221-BB-SETUP")
        assert bb_setup.status == TaskStatus.TODO

    def test_complete_task_cascade_multiple_levels(self, populated_service):
        """Test that completing tasks doesn't cascade beyond immediate dependencies."""
        # First complete SYLLABUS
        populated_service.complete_task("MATH221-SYLLABUS")

        # Then complete BB-SETUP - should only unblock GRADEBOOK, not ASSIGNMENT
        result = populated_service.complete_task("MATH221-BB-SETUP")

        assert result["unblocked_count"] == 1
        assert result["unblocked_tasks"][0]["id"] == "MATH221-BB-GRADEBOOK"

        # ASSIGNMENT should still be blocked
        graph = populated_service.build_task_graph()
        assignment = graph.get_task("MATH221-BB-ASSIGNMENT")
        assert assignment.status == TaskStatus.BLOCKED

    def test_update_task_status_prevents_invalid_transitions(self, populated_service):
        """Test that blocked tasks cannot be started."""
        # Try to start a blocked task
        result = populated_service.update_task_status("MATH221-BB-GRADEBOOK", "in_progress")

        assert "error" in result
        assert "Cannot start blocked task" in result["error"]
        assert "Setup Blackboard" in result["blockers"][0]

    def test_update_task_status_unmarks_done(self, populated_service):
        """Test that unmarking a done task re-blocks dependencies."""
        # First complete the chain
        populated_service.complete_task("MATH221-SYLLABUS")
        populated_service.complete_task("MATH221-BB-SETUP")

        # Now unmark BB-SETUP as done
        result = populated_service.update_task_status("MATH221-BB-SETUP", "todo")

        # GRADEBOOK should be re-blocked
        assert len(result["affected_tasks"]) == 1
        assert result["affected_tasks"][0]["id"] == "MATH221-BB-GRADEBOOK"
        assert result["affected_tasks"][0]["status"] == "blocked"

    def test_get_critical_path(self, populated_service):
        """Test critical path calculation."""
        # The critical path should be the longest chain
        critical_path = populated_service.get_critical_path()

        # Should be SYLLABUS -> BB-SETUP -> GRADEBOOK -> ASSIGNMENT
        assert len(critical_path) == 4
        path_ids = [t["id"] for t in critical_path]
        assert path_ids == [
            "MATH221-SYLLABUS",
            "MATH221-BB-SETUP",
            "MATH221-BB-GRADEBOOK",
            "MATH221-BB-ASSIGNMENT",
        ]

    def test_get_critical_path_with_weights(self, populated_service):
        """Test critical path with different task weights."""
        # Modify weights to create a different critical path
        graph = populated_service.build_task_graph()
        graph.get_task("MATH221-BB-GRADEBOOK").weight = 10  # Make this heavy
        populated_service._save_graph(graph)

        critical_path = populated_service.get_critical_path()

        # Path should still be the same (only one path exists)
        # but the weight calculation should reflect the heavy task
        assert len(critical_path) == 4

    def test_get_dependency_stats(self, populated_service):
        """Test dependency statistics calculation."""
        stats = populated_service.get_dependency_stats()

        assert stats["total_tasks"] == 4
        assert stats["blocked_tasks"] == 3  # All except SYLLABUS
        assert stats["tasks_with_dependencies"] == 3
        assert stats["parent_tasks"] == 2  # SYLLABUS and BB-SETUP
        assert stats["child_tasks"] == 2  # GRADEBOOK and ASSIGNMENT
        assert stats["max_dependency_depth"] == 3  # Longest chain is 3 levels
        assert stats["critical_path_length"] == 4

    def test_validate_dependencies_valid_graph(self, populated_service):
        """Test dependency validation with a valid graph."""
        result = populated_service.validate_dependencies()

        assert result["valid"] is True
        assert result["issue_count"] == 0
        assert len(result["issues"]) == 0

    def test_validate_dependencies_missing_dependency(self, populated_service):
        """Test validation detects missing dependencies."""
        # Add a task with invalid dependency
        graph = populated_service.build_task_graph()
        bad_task = Task(
            id="BAD-TASK", course="MATH221", title="Bad Task", depends_on=["NON-EXISTENT-TASK"]
        )
        graph.add_task(bad_task)
        populated_service._save_graph(graph)

        result = populated_service.validate_dependencies()

        assert result["valid"] is False
        assert result["issue_count"] > 0

        # Find the missing dependency issue
        missing_issues = [i for i in result["issues"] if i["type"] == "missing_dependency"]
        assert len(missing_issues) == 1
        assert missing_issues[0]["missing_id"] == "NON-EXISTENT-TASK"

    def test_validate_dependencies_circular(self, populated_service):
        """Test validation detects circular dependencies."""
        # Create a circular dependency
        graph = populated_service.build_task_graph()

        # Make SYLLABUS depend on ASSIGNMENT (creating a cycle)
        syllabus = graph.get_task("MATH221-SYLLABUS")
        syllabus.depends_on = ["MATH221-BB-ASSIGNMENT"]
        populated_service._save_graph(graph)

        result = populated_service.validate_dependencies()

        assert result["valid"] is False
        circular_issues = [i for i in result["issues"] if i["type"] == "circular_dependency"]
        assert len(circular_issues) > 0

    def test_validate_dependencies_orphaned_parent(self, populated_service):
        """Test validation detects orphaned parent references."""
        graph = populated_service.build_task_graph()

        orphan = Task(
            id="ORPHAN", course="MATH221", title="Orphan Task", parent_id="NON-EXISTENT-PARENT"
        )
        graph.add_task(orphan)
        populated_service._save_graph(graph)

        result = populated_service.validate_dependencies()

        assert result["valid"] is False
        parent_issues = [i for i in result["issues"] if i["type"] == "missing_parent"]
        assert len(parent_issues) == 1
        assert parent_issues[0]["parent_id"] == "NON-EXISTENT-PARENT"

    @pytest.mark.parametrize(
        "depth,expected_max",
        [
            (1, 0),  # Single task, no dependencies
            (2, 1),  # Two tasks, one dependency
            (5, 4),  # Five tasks in a chain
        ],
    )
    def test_dependency_depth_calculation(self, setup_test_environment, depth, expected_max):
        """Test calculation of dependency depth with various chain lengths."""
        tasks_file = setup_test_environment

        # Create a chain of tasks with specified depth
        tasks = []
        for i in range(depth):
            task = {
                "id": f"TASK-{i}",
                "course": "TEST",
                "title": f"Task {i}",
                "status": "blocked" if i > 0 else "todo",
                "priority": "medium",
                "category": "setup",
                "depends_on": [f"TASK-{i - 1}"] if i > 0 else [],
                "parent_id": None,
            }
            tasks.append(task)

        data = {
            "tasks": tasks,
            "metadata": {"version": "2.0", "updated": datetime.now().isoformat()},
        }

        with open(tasks_file, "w") as f:
            json.dump(data, f)

        service = DependencyService()
        stats = service.get_dependency_stats()

        assert stats["max_dependency_depth"] == expected_max

    @pytest.mark.slow
    def test_large_graph_performance(self, setup_test_environment):
        """Test performance with a large task graph."""
        tasks_file = setup_test_environment

        # Create a large graph with 100 tasks
        tasks = []
        for i in range(100):
            task = {
                "id": f"TASK-{i:03d}",
                "course": "PERF",
                "title": f"Task {i}",
                "status": "todo",
                "priority": "medium",
                "category": "setup",
                "depends_on": [f"TASK-{i - 1:03d}"] if i > 0 and i % 3 != 0 else [],
                "parent_id": f"TASK-{i // 10:03d}" if i > 9 else None,
            }
            tasks.append(task)

        data = {
            "tasks": tasks,
            "metadata": {"version": "2.0", "updated": datetime.now().isoformat()},
        }

        with open(tasks_file, "w") as f:
            json.dump(data, f)

        service = DependencyService()

        # All operations should complete in reasonable time
        import time

        start = time.time()
        service.build_task_graph()
        assert time.time() - start < 1.0  # Should build in under 1 second

        start = time.time()
        service.get_task_hierarchy()
        assert time.time() - start < 1.0

        start = time.time()
        service.get_critical_path()
        assert time.time() - start < 2.0  # Critical path might take longer
