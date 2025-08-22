#!/usr/bin/env python3
"""
Generate tasks with dependency and hierarchy support.
Creates complex task graphs from YAML templates.
"""

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import yaml


class DependencyAwareTaskGenerator:
    """Generate tasks with parent-child relationships and dependencies."""

    def __init__(self, template_dir: Path, course_file: Path):
        self.template_dir = Path(template_dir)
        self.course_file = Path(course_file)
        self.tasks = {}
        self.key_to_id_map = {}

    def load_courses(self) -> list[dict[str, Any]]:
        """Load course configuration."""
        with open(self.course_file) as f:
            data = json.load(f)
        return data.get("courses", [])

    def load_templates(self) -> dict[str, list[dict[str, Any]]]:
        """Load all YAML task templates."""
        templates = {}

        for yaml_file in self.template_dir.glob("*.yaml"):
            with open(yaml_file) as f:
                template_data = yaml.safe_load(f)
                category = yaml_file.stem
                templates[category] = template_data.get("tasks", [])

        return templates

    def generate_task_id(self, course: str, key: str) -> str:
        """Generate a unique task ID from course and template key."""
        # Create deterministic IDs for dependency resolution
        return f"{course}-{key}".replace("_", "-").upper()

    def calculate_due_date(self, base_date: datetime, offset: dict[str, Any]) -> datetime:
        """Calculate due date from base date and offset specification."""
        if not offset:
            return None

        days = offset.get("days", 0)
        weeks = offset.get("weeks", 0)

        # Handle different base references
        offset.get("from", "semester.start_date")

        # For now, use base_date as semester start
        # In production, would look up actual dates from semester config
        result_date = base_date + timedelta(days=days, weeks=weeks)

        return result_date

    def create_task(
        self, template: dict[str, Any], course: dict[str, Any], semester_start: datetime
    ) -> dict[str, Any]:
        """Create a task from template and course data."""
        task_id = self.generate_task_id(course["code"], template["key"])

        # Store key to ID mapping for dependency resolution
        self.key_to_id_map[f"{course['code']}-{template['key']}"] = task_id

        task = {
            "id": task_id,
            "course": course["code"],
            "title": template["title"].format(course=course["name"]),
            "description": template.get("description", "").format(course=course["name"]),
            "category": template.get("category", "setup"),
            "priority": template.get("priority", "medium"),
            "status": "todo",  # Will be updated based on dependencies
            "weight": template.get("weight", 1),
            "assignee": template.get("assignee"),
            "parent_id": None,  # Will be resolved in second pass
            "depends_on": [],  # Will be resolved in second pass
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        # Calculate due date if specified
        if "due_offset" in template:
            due_date = self.calculate_due_date(semester_start, template["due_offset"])
            if due_date:
                task["due_date"] = due_date.date().isoformat()

        # Store template reference for relationship resolution
        task["_template"] = template
        task["_course_code"] = course["code"]

        return task

    def resolve_relationships(self):
        """Second pass to resolve parent and dependency relationships."""
        for _task_id, task in self.tasks.items():
            template = task.pop("_template", {})
            course_code = task.pop("_course_code", "")

            # Resolve parent relationship
            if "parent_key" in template:
                parent_key = f"{course_code}-{template['parent_key']}"
                parent_id = self.key_to_id_map.get(parent_key)
                if parent_id:
                    task["parent_id"] = parent_id

            # Resolve dependencies
            if "depends_on_keys" in template:
                for dep_key in template["depends_on_keys"]:
                    # Handle both local (same course) and cross-course dependencies
                    if "." in dep_key:
                        # Cross-course dependency: MATH251.BB-SETUP
                        dep_course, dep_task_key = dep_key.split(".")
                        full_key = f"{dep_course}-{dep_task_key}"
                    else:
                        # Same course dependency
                        full_key = f"{course_code}-{dep_key}"

                    dep_id = self.key_to_id_map.get(full_key)
                    if dep_id:
                        task["depends_on"].append(dep_id)

            # Update status based on dependencies
            if task["depends_on"]:
                task["status"] = "blocked"

    def generate_all_tasks(self, semester_start: datetime) -> dict[str, Any]:
        """Generate all tasks for all courses with relationships."""
        courses = self.load_courses()
        templates = self.load_templates()

        # First pass: Create all tasks
        for course in courses:
            for _category, category_templates in templates.items():
                for template in category_templates:
                    # Check if template applies to this course type
                    if "course_types" in template:
                        course_type = course.get("type", "standard")
                        if course_type not in template["course_types"]:
                            continue

                    task = self.create_task(template, course, semester_start)
                    self.tasks[task["id"]] = task

        # Second pass: Resolve relationships
        self.resolve_relationships()

        # Create final output structure
        return {
            "tasks": list(self.tasks.values()),
            "metadata": {
                "version": "2.0",
                "generated": datetime.now().isoformat(),
                "total_tasks": len(self.tasks),
                "courses": [c["code"] for c in courses],
                "has_dependencies": True,
            },
        }

    def validate_dependencies(self) -> list[str]:
        """Validate that all dependencies can be resolved."""
        issues = []

        for task_id, task in self.tasks.items():
            # Check for missing dependencies
            for dep_id in task.get("depends_on", []):
                if dep_id not in self.tasks:
                    issues.append(f"Task {task_id} depends on non-existent task {dep_id}")

            # Check for missing parent
            parent_id = task.get("parent_id")
            if parent_id and parent_id not in self.tasks:
                issues.append(f"Task {task_id} has non-existent parent {parent_id}")

        # Check for circular dependencies (simplified)
        def has_circular_dep(task_id, visited=None):
            if visited is None:
                visited = set()

            if task_id in visited:
                return True

            visited.add(task_id)
            task = self.tasks.get(task_id, {})

            for dep_id in task.get("depends_on", []):
                if has_circular_dep(dep_id, visited.copy()):
                    issues.append(f"Circular dependency detected involving {task_id}")
                    return True

            return False

        for task_id in self.tasks:
            has_circular_dep(task_id)

        return issues


def main():
    """Main entry point for task generation."""
    parser = argparse.ArgumentParser(description="Generate tasks with dependencies")
    parser.add_argument(
        "--templates",
        type=Path,
        default="templates/tasks",
        help="Directory containing task template YAML files",
    )
    parser.add_argument(
        "--courses", type=Path, default="content/courses.json", help="Course configuration file"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default="dashboard/state/tasks.json",
        help="Output file for generated tasks",
    )
    parser.add_argument(
        "--semester-start", type=str, default="2025-08-25", help="Semester start date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--validate", action="store_true", help="Validate dependencies after generation"
    )

    args = parser.parse_args()

    # Parse semester start date
    semester_start = datetime.fromisoformat(args.semester_start)

    # Generate tasks
    generator = DependencyAwareTaskGenerator(args.templates, args.courses)
    task_data = generator.generate_all_tasks(semester_start)

    # Validate if requested
    if args.validate:
        issues = generator.validate_dependencies()
        if issues:
            print("Validation issues found:")
            for issue in issues:
                print(f"  - {issue}")
            return 1
        else:
            print("✓ All dependencies valid")

    # Save output
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(task_data, f, indent=2)

    print(f"Generated {len(task_data['tasks'])} tasks")
    print(f"Output saved to: {args.output}")

    # Print statistics
    blocked_count = sum(1 for t in task_data["tasks"] if t["status"] == "blocked")
    parent_count = sum(1 for t in task_data["tasks"] if not t.get("parent_id"))

    print(f"  - Parent tasks: {parent_count}")
    print(f"  - Child tasks: {len(task_data['tasks']) - parent_count}")
    print(f"  - Blocked tasks: {blocked_count}")

    return 0


if __name__ == "__main__":
    exit(main())
