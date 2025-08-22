#!/usr/bin/env python3
"""
Validate task data integrity and dependencies.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


class TaskValidator:
    """Validate task data structure and dependencies."""

    def __init__(self, tasks_file: str = "dashboard/state/tasks.json"):
        self.tasks_file = Path(tasks_file)
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def validate(self) -> bool:
        """Run all validations."""
        if not self.tasks_file.exists():
            self.errors.append(f"Tasks file not found: {self.tasks_file}")
            return False

        try:
            with open(self.tasks_file) as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON: {e}")
            return False

        tasks = data.get("tasks", [])

        # Run validations
        self._validate_required_fields(tasks)
        self._validate_dependencies(tasks)
        self._validate_dates(tasks)
        self._validate_statuses(tasks)
        self._check_duplicates(tasks)
        self._check_circular_dependencies(tasks)

        # Print results
        self._print_results()

        return len(self.errors) == 0

    def _validate_required_fields(self, tasks: list[dict[str, Any]]) -> None:
        """Check required fields are present."""
        required = ["id", "title", "status", "course"]

        for task in tasks:
            for field in required:
                if field not in task:
                    self.errors.append(
                        f"Task {task.get('id', 'UNKNOWN')} missing required field: {field}"
                    )

    def _validate_dependencies(self, tasks: list[dict[str, Any]]) -> None:
        """Check all dependencies exist."""
        task_ids = {task["id"] for task in tasks}

        for task in tasks:
            if "blocked_by" in task:
                for dep_id in task["blocked_by"]:
                    if dep_id not in task_ids:
                        self.errors.append(
                            f"Task {task['id']} depends on non-existent task: {dep_id}"
                        )

    def _validate_dates(self, tasks: list[dict[str, Any]]) -> None:
        """Validate date formats and logic."""
        now = datetime.now()

        for task in tasks:
            if "due" in task:
                try:
                    due = datetime.fromisoformat(task["due"])

                    # Warn about past due dates for non-completed tasks
                    if due < now and task.get("status") not in ["done", "review"]:
                        self.warnings.append(f"Task {task['id']} is overdue ({due.date()})")

                except (ValueError, TypeError):
                    self.errors.append(f"Task {task['id']} has invalid due date: {task['due']}")

    def _validate_statuses(self, tasks: list[dict[str, Any]]) -> None:
        """Validate task statuses."""
        valid_statuses = {"blocked", "todo", "doing", "review", "done"}

        for task in tasks:
            status = task.get("status")
            if status not in valid_statuses:
                self.errors.append(f"Task {task['id']} has invalid status: {status}")

            # Check blocked tasks have dependencies
            if status == "blocked" and not task.get("blocked_by"):
                self.warnings.append(f"Task {task['id']} is blocked but has no dependencies")

    def _check_duplicates(self, tasks: list[dict[str, Any]]) -> None:
        """Check for duplicate task IDs."""
        seen = set()
        for task in tasks:
            task_id = task.get("id")
            if task_id in seen:
                self.errors.append(f"Duplicate task ID: {task_id}")
            seen.add(task_id)

    def _check_circular_dependencies(self, tasks: list[dict[str, Any]]) -> None:
        """Check for circular dependency chains."""
        # Build dependency graph
        deps = {}
        for task in tasks:
            task_id = task.get("id")
            deps[task_id] = task.get("blocked_by", [])

        # DFS to find cycles
        def has_cycle(node: str, visited: set[str], stack: set[str]) -> bool:
            visited.add(node)
            stack.add(node)

            for neighbor in deps.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor, visited, stack):
                        return True
                elif neighbor in stack:
                    return True

            stack.remove(node)
            return False

        visited: set[str] = set()
        for task_id in deps:
            if task_id and task_id not in visited and has_cycle(task_id, visited, set()):
                self.errors.append(f"Circular dependency detected involving task: {task_id}")

    def _print_results(self) -> None:
        """Print validation results."""
        if self.errors:
            print("❌ Validation FAILED\n")
            print("Errors:")
            for error in self.errors:
                print(f"  • {error}")

        if self.warnings:
            print("\n⚠️  Warnings:")
            for warning in self.warnings:
                print(f"  • {warning}")

        if not self.errors and not self.warnings:
            print("✅ Validation passed - all tasks valid")


def main() -> None:
    """CLI entry point."""
    validator = TaskValidator()

    if validator.validate():
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()


# ------------------------
# Lightweight helper APIs
# ------------------------


def validate_task_structure(task: dict[str, Any]) -> bool:
    """Validate a single task has the core required fields.

    Required: id, course, title, status, priority, category
    Optional: due_date (ISO date)
    """
    required = ["id", "course", "title", "status", "priority", "category"]
    for field in required:
        if field not in task:
            return False
    # If due_date present, verify format
    if "due_date" in task:
        try:
            datetime.fromisoformat(task["due_date"])  # type: ignore[arg-type]
        except Exception:
            return False
    return True


def validate_dates(tasks: list[dict[str, Any]]) -> list[str]:
    """Return list of error messages for invalid due_date values."""
    errors: list[str] = []
    for t in tasks:
        if "due_date" in t:
            try:
                datetime.fromisoformat(t["due_date"])  # type: ignore[arg-type]
            except Exception:
                errors.append(f"Task {t.get('id')} has invalid due_date: {t.get('due_date')}")
    return errors


def check_duplicates(tasks: list[dict[str, Any]]) -> list[str]:
    """Return list of duplicate task IDs."""
    seen: set[str] = set()
    dups: list[str] = []
    for t in tasks:
        tid = t.get("id")
        if tid in seen:
            dups.append(tid)  # type: ignore[arg-type]
        if tid is not None:
            seen.add(tid)
    return dups


def validate_dependencies(tasks: list[dict[str, Any]]) -> list[str]:
    """Return list of errors for depends_on IDs that do not exist."""
    errors: list[str] = []
    ids = {t.get("id") for t in tasks}
    for t in tasks:
        deps = t.get("depends_on", []) or []
        for dep in deps:
            if dep not in ids:
                errors.append(f"Task {t.get('id')} depends on missing task: {dep}")
    return errors


def validate_all(tasks_file: Path | str) -> dict[str, Any]:
    """Validate a tasks.json file and return summary info used by tests."""
    data = json.loads(Path(tasks_file).read_text())
    tasks = data.get("tasks", [])
    errors: list[str] = []
    # Structure
    for t in tasks:
        if not validate_task_structure(t):
            errors.append(f"Task {t.get('id')} has invalid structure")
    # Dates
    errors.extend(validate_dates(tasks))
    # Duplicates
    dups = check_duplicates(tasks)
    errors.extend([f"Duplicate task ID: {d}" for d in dups])
    # Dependencies
    errors.extend(validate_dependencies(tasks))

    return {"valid": len(errors) == 0, "error_count": len(errors), "errors": errors}
