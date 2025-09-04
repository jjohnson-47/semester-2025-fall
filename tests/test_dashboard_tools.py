#!/usr/bin/env python3
"""
Tests for dashboard tool scripts.
Tests task generation, validation, and export functionality.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def mock_courses_data():
    """Sample courses configuration."""
    return {
        "courses": [
            {
                "code": "MATH221",
                "name": "Calculus I",
                "instructor": "Dr. Smith",
                "credits": 4,
                "meeting_times": "MWF 10:00-11:00",
            },
            {
                "code": "MATH251",
                "name": "Calculus II",
                "instructor": "Dr. Johnson",
                "credits": 4,
                "meeting_times": "TTh 2:00-3:30",
            },
        ]
    }


@pytest.fixture
def mock_template_data():
    """Sample task templates."""
    return {
        "templates": [
            {
                "id": "syllabus",
                "title": "Create course syllabus",
                "category": "setup",
                "priority": "high",
                "days_before_start": 14,
                "description": "Draft and finalize syllabus",
            },
            {
                "id": "blackboard",
                "title": "Setup Blackboard shell",
                "category": "technical",
                "priority": "high",
                "days_before_start": 10,
                "description": "Configure online course components",
            },
        ]
    }


class TestGenerateTasks:
    """Test the generate_tasks.py tool."""

    @pytest.mark.unit
    def test_load_templates(self, tmp_path, mock_template_data):
        """Test loading task templates."""
        from dashboard.tools.generate_tasks import load_templates

        template_file = tmp_path / "templates.json"
        template_file.write_text(json.dumps(mock_template_data))

        templates = load_templates(template_file)
        assert len(templates) == 2
        assert templates[0]["id"] == "syllabus"

    @pytest.mark.unit
    def test_generate_task_from_template(self):
        """Test generating a task from template."""
        from dashboard.tools.generate_tasks import generate_task_from_template

        template = {
            "id": "test-template",
            "title": "Test task {course}",
            "category": "test",
            "priority": "medium",
            "days_before_start": 5,
        }

        course = {"code": "MATH221", "name": "Calculus I"}
        start_date = datetime(2025, 8, 25)

        task = generate_task_from_template(template, course, start_date)

        assert task["title"] == "Test task MATH221"
        assert task["course"] == "MATH221"
        assert task["priority"] == "medium"
        assert task["due_date"] == "2025-08-20"

    @pytest.mark.unit
    def test_generate_all_tasks(self, mock_courses_data, mock_template_data):
        """Test generating tasks for all courses."""
        from dashboard.tools.generate_tasks import generate_all_tasks

        start_date = datetime(2025, 8, 25)
        tasks = generate_all_tasks(
            mock_courses_data["courses"], mock_template_data["templates"], start_date
        )

        # Should generate 2 templates × 2 courses = 4 tasks
        assert len(tasks) == 4

        # Check task properties
        math221_tasks = [t for t in tasks if t["course"] == "MATH221"]
        assert len(math221_tasks) == 2

        # Verify unique IDs
        task_ids = [t["id"] for t in tasks]
        assert len(task_ids) == len(set(task_ids))

    @pytest.mark.integration
    def test_main_generation_flow(self, tmp_path, mock_courses_data, mock_template_data):
        """Test complete task generation workflow."""
        from dashboard.tools.generate_tasks import main

        # Setup test files
        courses_file = tmp_path / "courses.json"
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        output_file = tmp_path / "tasks.json"

        courses_file.write_text(json.dumps(mock_courses_data))
        (templates_dir / "setup.json").write_text(json.dumps(mock_template_data))

        # Run generation
        with patch(
            "sys.argv",
            [
                "generate_tasks.py",
                "--courses",
                str(courses_file),
                "--templates",
                str(templates_dir),
                "--out",
                str(output_file),
            ],
        ):
            result = main()
            assert result == 0

        # Verify output
        assert output_file.exists()
        tasks_data = json.loads(output_file.read_text())
        assert "tasks" in tasks_data
        assert "metadata" in tasks_data


class TestValidateTool:
    """Test the validate.py tool."""

    @pytest.mark.unit
    def test_validate_task_structure(self):
        """Test validation of task data structure."""
        from dashboard.tools.validate import validate_task_structure

        # Valid task
        valid_task = {
            "id": "task-001",
            "course": "MATH221",
            "title": "Test task",
            "status": "todo",
            "priority": "high",
            "category": "setup",
            "due_date": "2025-08-20",
        }
        assert validate_task_structure(valid_task) is True

        # Invalid task (missing required field)
        invalid_task = {"id": "task-001", "course": "MATH221", "status": "todo"}
        assert validate_task_structure(invalid_task) is False

    @pytest.mark.unit
    def test_validate_dates(self):
        """Test date validation."""
        from dashboard.tools.validate import validate_dates

        tasks = [
            {"id": "1", "due_date": "2025-08-20"},
            {"id": "2", "due_date": "2025-08-25"},
            {"id": "3", "due_date": "invalid-date"},
        ]

        errors = validate_dates(tasks)
        assert len(errors) == 1
        assert "invalid-date" in errors[0]

    @pytest.mark.unit
    def test_check_duplicates(self):
        """Test duplicate ID detection."""
        from dashboard.tools.validate import check_duplicates

        tasks = [
            {"id": "task-001", "title": "Task 1"},
            {"id": "task-002", "title": "Task 2"},
            {"id": "task-001", "title": "Duplicate"},
        ]

        duplicates = check_duplicates(tasks)
        assert len(duplicates) == 1
        assert "task-001" in duplicates

    @pytest.mark.unit
    def test_validate_dependencies(self):
        """Test task dependency validation."""
        from dashboard.tools.validate import validate_dependencies

        tasks = [
            {"id": "task-001", "depends_on": []},
            {"id": "task-002", "depends_on": ["task-001"]},
            {"id": "task-003", "depends_on": ["task-999"]},  # Invalid dependency
        ]

        errors = validate_dependencies(tasks)
        assert len(errors) == 1
        assert "task-999" in errors[0]

    @pytest.mark.integration
    def test_full_validation(self, tmp_path):
        """Test complete validation workflow."""
        from dashboard.tools.validate import validate_all

        tasks_data = {
            "tasks": [
                {
                    "id": "task-001",
                    "course": "MATH221",
                    "title": "Valid task",
                    "status": "todo",
                    "priority": "high",
                    "category": "setup",
                    "due_date": "2025-08-20",
                }
            ],
            "metadata": {"version": "1.0", "updated": datetime.now().isoformat()},
        }

        tasks_file = tmp_path / "tasks.json"
        tasks_file.write_text(json.dumps(tasks_data))

        result = validate_all(tasks_file)
        assert result["valid"] is True
        assert result["error_count"] == 0


class TestDashboardHelpers:
    """Test shared helper functions."""

    @pytest.mark.unit
    def test_generate_task_id(self):
        """Test unique ID generation."""
        from dashboard.tools.helpers import generate_task_id

        ids = [generate_task_id() for _ in range(100)]

        # All IDs should be unique
        assert len(ids) == len(set(ids))

        # IDs should follow expected format
        for task_id in ids:
            assert task_id.startswith("task-")
            assert len(task_id) > 5

    @pytest.mark.unit
    def test_calculate_due_date(self):
        """Test due date calculation."""
        from dashboard.tools.helpers import calculate_due_date

        start_date = datetime(2025, 8, 25)

        # 10 days before start
        due_date = calculate_due_date(start_date, days_before=10)
        assert due_date == datetime(2025, 8, 15)

        # 5 days after start
        due_date = calculate_due_date(start_date, days_after=5)
        assert due_date == datetime(2025, 8, 30)

    @pytest.mark.unit
    def test_format_date_for_display(self):
        """Test date formatting for display."""
        from dashboard.tools.helpers import format_date_for_display

        date = datetime(2025, 8, 25, 14, 30)

        # Default format
        formatted = format_date_for_display(date)
        assert "Aug" in formatted or "08" in formatted
        assert "25" in formatted

        # Custom format
        formatted = format_date_for_display(date, fmt="%Y-%m-%d")
        assert formatted == "2025-08-25"

    @pytest.mark.unit
    def test_priority_sort_key(self):
        """Test priority-based sorting."""
        from dashboard.tools.helpers import priority_sort_key

        tasks = [
            {"id": "1", "priority": "low"},
            {"id": "2", "priority": "high"},
            {"id": "3", "priority": "medium"},
            {"id": "4", "priority": "critical"},
        ]

        sorted_tasks = sorted(tasks, key=priority_sort_key)

        # Should be sorted: critical, high, medium, low
        assert sorted_tasks[0]["priority"] == "critical"
        assert sorted_tasks[1]["priority"] == "high"
        assert sorted_tasks[2]["priority"] == "medium"
        assert sorted_tasks[3]["priority"] == "low"


@pytest.mark.smoke
class TestSmokeTests:
    """Quick smoke tests for CI."""

    def test_imports(self):
        """Test that all modules can be imported."""
        try:
            # Test imports by verifying app exists
            from dashboard.app import app
            assert hasattr(app, "route")

            from dashboard.tools import generate_tasks, validate

            # These modules should be importable even if we don't use them directly
            assert generate_tasks is not None
            assert validate is not None
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

    def test_flask_app_exists(self):
        """Test Flask app is properly configured."""
        from dashboard.app import app

        assert app is not None
        assert app.name == "dashboard.app" or "app" in app.name

    def test_basic_config(self):
        """Test basic configuration is present."""
        from dashboard.app import STATE_DIR, TIMEZONE

        assert TIMEZONE is not None
        assert STATE_DIR is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
