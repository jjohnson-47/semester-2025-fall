#!/usr/bin/env python3
"""
Generate tasks from templates and course configuration.

This module exposes simple helper functions used by tests:
- load_templates: load JSON templates from a file
- generate_task_from_template: build a task dict from a template + course
- generate_all_tasks: create tasks for all courses and templates
- main: CLI entry point that reads JSON templates in a directory and writes tasks

It also contains a more advanced YAML-driven TaskGenerator used by the Makefile
pipeline. The helpers are intentionally lightweight and JSON-focused for tests.
"""

import argparse
import json
import logging
import os
import re
import sys
from collections.abc import Iterable
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

# Set up logging
logger = logging.getLogger(__name__)


class TaskGenerator:
    """Generate tasks from YAML templates."""

    def __init__(self, courses_file: str, templates_dir: str):
        self.courses = self._load_json(courses_file)
        self.templates_dir = Path(templates_dir)
        self.tasks: list[dict[str, Any]] = []
        self.task_counter = 0

    def _load_json(self, filepath: str) -> dict[str, Any]:
        """Load JSON file."""
        with open(filepath) as f:
            data: dict[str, Any] = json.load(f)
            return data

    def _load_yaml(self, filepath: str) -> dict[str, Any]:
        """Load YAML file."""
        with open(filepath) as f:
            data: dict[str, Any] = yaml.safe_load(f)
            return data

    def generate(self) -> dict[str, Any]:
        """Generate all tasks from templates."""
        # Process each template file
        template_files = sorted(self.templates_dir.glob("*.yaml"))

        for template_file in template_files:
            print(f"Processing template: {template_file.name}")
            self._process_template(template_file)

        # Sort tasks by due date and priority
        self.tasks.sort(key=lambda t: (t.get("due", "9999-12-31"), -t.get("weight", 1)))

        return {
            "tasks": self.tasks,
            "metadata": {
                "version": "1.0",
                "generated": datetime.now().isoformat(),
                "semester": self.courses.get("semester", "2025-fall"),
                "task_count": len(self.tasks),
            },
        }

    def _process_template(self, template_file: Path) -> None:
        """Process a single template file."""
        # Load YAML, handling multiple documents separated by ---
        with open(template_file) as f:
            yaml_docs = list(yaml.safe_load_all(f))

        for template in yaml_docs:
            if not template:  # Skip empty documents
                continue

            # Get applicable courses
            applies_to = template.get("applies_to", [])
            if "ALL" in applies_to:
                applies_to = [c["code"] for c in self.courses.get("courses", [])]

            # Generate tasks for each applicable course
            for course_code in applies_to:
                course = self._get_course(course_code)
                if not course:
                    print(f"  Warning: Course {course_code} not found")
                    continue

                for task_template in template.get("tasks", []):
                    task = self._create_task(task_template, template, course)
                    self.tasks.append(task)
                    print(f"  Created task: {task['id']}")

    def _get_course(self, course_code: str) -> dict[str, Any] | None:
        """Get course by code."""
        for course in self.courses.get("courses", []):
            if course["code"] == course_code:
                return dict(course)
        return None

    def _create_task(
        self, task_template: dict[str, Any], template: dict[str, Any], course: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a task from template."""
        self.task_counter += 1

        # Prepare context for variable substitution
        context = {
            "course": course,
            "semester": self.courses.get("important_dates", {}),
        }

        # Generate task ID - use provided ID or construct from key
        if "id" in task_template:
            task_id = self._substitute_vars(task_template["id"], context)
        else:
            task_key = task_template.get("key", f"TASK-{self.task_counter:04d}")
            task_id = f"{course['code']}-{task_key}"

        # Calculate due date
        due_date = self._calculate_due_date(task_template.get("due_offset", {}))

        # Get category from task or defaults
        category = task_template.get(
            "category", template.get("defaults", {}).get("category", "setup")
        )

        # Create task
        task = {
            "id": task_id,
            "course": course["code"],
            "title": self._substitute_vars(task_template["title"], context),
            "description": self._substitute_vars(task_template.get("description", ""), context),
            "category": category,
            "status": "blocked" if task_template.get("blocked_by") else "todo",
            "priority": "medium",  # Default priority
            "weight": task_template.get("weight", template.get("defaults", {}).get("weight", 1)),
            "tags": task_template.get("tags", template.get("defaults", {}).get("tags", [])),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "history": [],
        }

        # Add optional fields
        if due_date:
            task["due_date"] = due_date.isoformat()

        # Handle parent_id for hierarchical tasks
        if "parent_id" in task_template:
            task["parent_id"] = self._substitute_vars(task_template["parent_id"], context)
        else:
            task["parent_id"] = None

        # Convert blocked_by to depends_on (matching our models.py structure)
        if "blocked_by" in task_template:
            blocked_by = task_template["blocked_by"]
            deps = blocked_by if isinstance(blocked_by, list) else [blocked_by]
            task["depends_on"] = [self._substitute_vars(dep, context) for dep in deps]
        else:
            task["depends_on"] = []

        if "checklist" in task_template:
            task["checklist"] = [
                self._substitute_vars(item, context) for item in task_template["checklist"]
            ]

        if "links" in task_template:
            task["links"] = task_template["links"]

        return task

    def _calculate_due_date(self, offset: dict[str, Any]) -> datetime | None:
        """Calculate due date from offset specification."""
        if not offset:
            return None

        days = offset.get("days", 0)
        from_date = offset.get("from", "semester.first_day")

        # Get base date
        if from_date == "semester.first_day":
            base = self.courses.get("important_dates", {}).get("first_day", "2025-08-25")
        elif from_date == "semester.last_day":
            base = self.courses.get("important_dates", {}).get("last_day", "2025-12-13")
        elif from_date == "today":
            base = datetime.now().strftime("%Y-%m-%d")
        else:
            base = from_date

        # Parse and offset
        try:
            base_date = datetime.strptime(base, "%Y-%m-%d")
            return base_date + timedelta(days=days)
        except (ValueError, TypeError) as e:
            logger.debug(f"Failed to parse date '{base}' with offset {days}: {e}")
            return None

    def _substitute_vars(self, text: str, context: dict[str, Any]) -> str:
        """Substitute template variables."""
        if not text:
            return text

        def replacer(match: re.Match[str]) -> str:
            path = match.group(1).split(".")
            value: Any = context
            for key in path:
                if isinstance(value, dict):
                    value = value.get(key, match.group(0))
                else:
                    return match.group(0)
            return str(value)

        return re.sub(r"{{([\w.]+)}}", replacer, text)


# ------------------------
# Lightweight JSON helpers
# ------------------------


def load_templates(template_file: Path | str) -> list[dict[str, Any]]:
    """Load templates from a JSON file with a top-level 'templates' list."""
    path = Path(template_file)
    data = json.loads(path.read_text())
    templates = data.get("templates", [])
    if not isinstance(templates, list):
        raise ValueError("templates must be a list")
    return templates


def _compute_due_date_for_template(template: dict[str, Any], start_date: datetime) -> str | None:
    """Compute ISO date string based on days_before_start or days_after_start."""
    days_before = template.get("days_before_start")
    days_after = template.get("days_after_start")
    if isinstance(days_before, int):
        due_dt = start_date - timedelta(days=days_before)
    elif isinstance(days_after, int):
        due_dt = start_date + timedelta(days=days_after)
    else:
        return None
    return due_dt.strftime("%Y-%m-%d")


def generate_task_from_template(
    template: dict[str, Any], course: dict[str, Any], start_date: datetime
) -> dict[str, Any]:
    """Generate a single task from template for a given course.

    Expected template keys: id, title, category, priority, days_before_start|days_after_start
    """
    course_code = course.get("code", "COURSE")
    title = template.get("title", "").replace("{course}", course_code)
    task_id = f"{course_code}-{template.get('id', 'task')}"

    task: dict[str, Any] = {
        "id": task_id,
        "course": course_code,
        "title": title,
        "status": "todo",
        "priority": template.get("priority", "medium"),
        "category": template.get("category", "setup"),
    }

    due = _compute_due_date_for_template(template, start_date)
    if due:
        task["due_date"] = due

    return task


def generate_all_tasks(
    courses: Iterable[dict[str, Any]],
    templates: Iterable[dict[str, Any]],
    start_date: datetime,
) -> list[dict[str, Any]]:
    """Generate tasks for each course-template pair with unique IDs."""
    tasks: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for course in courses:
        for template in templates:
            task = generate_task_from_template(template, course, start_date)
            # Ensure unique ID
            base_id = task["id"]
            if base_id in seen_ids:
                i = 2
                new_id = f"{base_id}-{i}"
                while new_id in seen_ids:
                    i += 1
                    new_id = f"{base_id}-{i}"
                task["id"] = new_id
            seen_ids.add(task["id"])
            tasks.append(task)
    return tasks


def main() -> int:
    """CLI entry point used by tests.

    Reads a JSON courses file and a directory of JSON files containing
    a top-level 'templates' list. Writes consolidated tasks JSON to --out.
    Returns 0 on success, nonzero on failure.
    """
    parser = argparse.ArgumentParser(description="Generate tasks from templates")
    parser.add_argument("--courses", required=True, help="Courses JSON file")
    parser.add_argument("--templates", required=True, help="Templates directory")
    parser.add_argument("--out", required=True, help="Output tasks JSON file")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Validate inputs
    if not Path(args.courses).exists():
        print(f"Error: Courses file not found: {args.courses}")
        return 1

    if not Path(args.templates).exists():
        print(f"Error: Templates directory not found: {args.templates}")
        return 1

    # Load inputs (JSON path for this CLI)
    courses_data = json.loads(Path(args.courses).read_text())
    all_templates: list[dict[str, Any]] = []
    for f in sorted(Path(args.templates).glob("*.json")):
        try:
            all_templates.extend(load_templates(f))
        except Exception as exc:  # pragma: no cover - defensive
            print(f"Warning: skipping template file {f}: {exc}")

    # Choose a start date: default to first day from variables if present
    start_date_str = (
        courses_data.get("important_dates", {}).get("first_day")
        or os.environ.get("SEMESTER_FIRST_DAY")
        or datetime.now().strftime("%Y-%m-%d")
    )
    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    except ValueError:
        start_date = datetime.now()

    # Generate tasks
    tasks = generate_all_tasks(courses_data.get("courses", []), all_templates, start_date)
    result = {
        "tasks": tasks,
        "metadata": {
            "version": "1.0",
            "generated": datetime.now().isoformat(),
            "task_count": len(tasks),
        },
    }

    # Write output
    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as file_handle:
        json.dump(result, file_handle, indent=2)

    print(f"\n✓ Generated {len(result['tasks'])} tasks")
    print(f"✓ Written to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
