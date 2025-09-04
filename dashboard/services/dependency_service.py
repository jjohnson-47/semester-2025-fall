#!/usr/bin/env python3
"""
Dependency resolution service for task management.
Handles complex task relationships and auto-unlocking.
"""

import contextlib
from datetime import datetime
from typing import Any

from dashboard.config import Config

# Legacy TaskService removed; dependency service operates on DB exclusively.
from dashboard.db import Database, DatabaseConfig
from dashboard.models import Task, TaskGraph, TaskStatus

_db = Database(DatabaseConfig(Config.STATE_DIR / "tasks.db"))
with contextlib.suppress(Exception):  # ensure schema exists
    _db.initialize()


def _status_db_to_model(s: str) -> str:
    """Map DB canonical status to TaskStatus string for model."""
    if s == "doing":
        return "in_progress"
    if s == "done":
        return "done"
    if s == "review":
        return "in_progress"
    return s


def _status_model_to_db(s: str) -> str:
    """Map TaskStatus string to DB canonical status."""
    if s == "in_progress":
        return "doing"
    if s == "done":
        return "done"
    if s == "blocked":
        return "blocked"
    if s == "todo":
        return "todo"
    return "todo"


class DependencyService:
    """Service for managing task dependencies and relationships."""

    @staticmethod
    def build_task_graph() -> TaskGraph:
        """Build a complete task graph from storage (DB if forced, else JSON)."""
        graph = TaskGraph()
        if Config.API_FORCE_DB:
            tasks = _db.list_tasks()
            # Load deps
            with _db.connect() as conn:
                rows = conn.execute("select task_id, blocks_id from deps").fetchall()
            dep_map: dict[str, list[str]] = {}
            for r in rows:
                dep_map.setdefault(r["task_id"], []).append(r["blocks_id"])  # type: ignore[index]
            for t in tasks:
                model_dict = {
                    "id": t.get("id"),
                    "course": t.get("course"),
                    "title": t.get("title"),
                    "status": _status_db_to_model(str(t.get("status", "todo"))),
                    "category": (t.get("category") or "setup"),
                    "parent_id": t.get("parent_id"),
                    "depends_on": dep_map.get(t.get("id"), []),
                    "description": t.get("notes"),
                    "weight": int(float(t.get("weight") or 1.0)),
                    "due_date": t.get("due_at"),
                    "created_at": t.get("created_at"),
                    "updated_at": t.get("updated_at"),
                }
                try:
                    task = Task.from_dict(model_dict)
                except Exception:
                    # Fallback minimal fields
                    task = Task(
                        id=str(t.get("id")), course=str(t.get("course")), title=str(t.get("title"))
                    )
                graph.add_task(task)
            return graph
        else:
            # Fallback: no JSON path in v2 cleanup; return empty graph
            return graph

    @staticmethod
    def get_task_hierarchy(course: str | None = None) -> dict[str, Any]:
        """
        Get tasks organized in a hierarchical structure.
        Returns a tree structure suitable for rendering.
        """
        graph = DependencyService.build_task_graph()

        # Filter by course if specified
        tasks = list(graph.tasks.values())
        if course:
            tasks = [t for t in tasks if t.course == course]

        # Build hierarchy
        hierarchy: dict[str, Any] = {"root_tasks": [], "task_map": {}, "children_map": {}}

        for task in tasks:
            task_dict = task.to_dict()
            task_dict["children"] = []
            task_dict["is_blocked"] = task.is_blocked()
            task_dict["blocker_titles"] = [
                blocker.title
                for dep_id in task.depends_on
                if (blocker := graph.get_task(dep_id)) is not None
            ]

            hierarchy["task_map"][task.id] = task_dict

            if task.parent_id:
                if task.parent_id not in hierarchy["children_map"]:
                    hierarchy["children_map"][task.parent_id] = []
                hierarchy["children_map"][task.parent_id].append(task.id)
            else:
                hierarchy["root_tasks"].append(task_dict)

        # Populate children arrays
        for parent_id, child_ids in hierarchy["children_map"].items():
            if parent_id in hierarchy["task_map"]:
                parent = hierarchy["task_map"][parent_id]
                parent["children"] = [
                    hierarchy["task_map"][child_id]
                    for child_id in child_ids
                    if child_id in hierarchy["task_map"]
                ]

        return hierarchy

    @staticmethod
    def complete_task(task_id: str) -> dict[str, Any]:
        """
        Mark a task as complete and handle dependency unlocking.
        Returns the completed task and any newly unblocked tasks.
        """
        graph = DependencyService.build_task_graph()
        task = graph.get_task(task_id)

        if not task:
            return {"error": "Task not found"}

        # Mark as completed and get unblocked tasks
        unblocked_tasks = graph.mark_completed(task_id)

        # Save updated tasks
        DependencyService._save_graph(graph)

        return {
            "completed_task": task.to_dict(),
            "unblocked_tasks": [t.to_dict() for t in unblocked_tasks],
            "unblocked_count": len(unblocked_tasks),
        }

    @staticmethod
    def update_task_status(task_id: str, new_status: str) -> dict[str, Any]:
        """
        Update task status with dependency checking.
        Returns updated task and affected tasks.
        """
        graph = DependencyService.build_task_graph()
        task = graph.get_task(task_id)

        if not task:
            return {"error": "Task not found"}

        # Don't allow starting blocked tasks
        if task.is_blocked() and new_status in ["in_progress", "done"]:
            return {
                "error": "Cannot start blocked task",
                "blockers": [
                    blocker.title
                    for dep_id in task.depends_on
                    if (blocker := graph.get_task(dep_id)) is not None
                ],
            }

        old_status = task.status
        task.status = TaskStatus(new_status)
        task.updated_at = datetime.now()

        affected_tasks = []

        # If marking as done, check for unblocked tasks
        if new_status == "done":
            task.completed_at = datetime.now()
            completed_ids = graph._get_completed_task_ids()

            for blocked_task in graph.get_blocked_by(task_id):
                if blocked_task.update_status_from_dependencies(completed_ids):
                    affected_tasks.append(blocked_task.to_dict())

        # If unmarking as done, check if we need to re-block tasks
        elif old_status == TaskStatus.DONE and new_status != "done":
            task.completed_at = None
            completed_ids = graph._get_completed_task_ids()

            for dependent_task in graph.get_blocked_by(task_id):
                if dependent_task.update_status_from_dependencies(completed_ids):
                    affected_tasks.append(dependent_task.to_dict())

        # Save updated tasks
        DependencyService._save_graph(graph)

        return {
            "updated_task": task.to_dict(),
            "affected_tasks": affected_tasks,
            "affected_count": len(affected_tasks),
        }

    @staticmethod
    def get_critical_path(course: str | None = None) -> list[dict[str, Any]]:
        """Get the critical path for a course or all tasks."""
        graph = DependencyService.build_task_graph()

        if course:
            # Filter graph to course-specific tasks
            course_graph = TaskGraph()
            for task in graph.tasks.values():
                if task.course == course:
                    course_graph.add_task(task)
            graph = course_graph

        critical_tasks = graph.get_critical_path()
        return [t.to_dict() for t in critical_tasks]

    @staticmethod
    def get_dependency_stats() -> dict[str, Any]:
        """Get statistics about task dependencies."""
        graph = DependencyService.build_task_graph()

        blocked_count = sum(1 for t in graph.tasks.values() if t.is_blocked())
        tasks_with_deps = sum(1 for t in graph.tasks.values() if t.depends_on)
        parent_tasks = sum(1 for t in graph.tasks.values() if not t.parent_id)

        # Find longest dependency chain
        max_chain_length = 0
        for task in graph.tasks.values():
            chain_length = DependencyService._get_dependency_depth(graph, task.id)
            max_chain_length = max(max_chain_length, chain_length)

        return {
            "total_tasks": len(graph.tasks),
            "blocked_tasks": blocked_count,
            "tasks_with_dependencies": tasks_with_deps,
            "parent_tasks": parent_tasks,
            "child_tasks": len(graph.tasks) - parent_tasks,
            "max_dependency_depth": max_chain_length,
            "critical_path_length": len(graph.get_critical_path()),
        }

    @staticmethod
    def validate_dependencies() -> dict[str, Any]:
        """
        Validate the dependency graph for issues.
        Checks for cycles, missing dependencies, etc.
        """
        graph = DependencyService.build_task_graph()
        issues = []

        # Check for missing dependencies
        for task in graph.tasks.values():
            for dep_id in task.depends_on:
                if dep_id not in graph.tasks:
                    issues.append(
                        {
                            "type": "missing_dependency",
                            "task_id": task.id,
                            "missing_id": dep_id,
                            "message": f"Task '{task.title}' depends on non-existent task '{dep_id}'",
                        }
                    )

        # Check for circular dependencies
        visited = set()
        rec_stack = set()

        def has_cycle(task_id: str) -> bool:
            visited.add(task_id)
            rec_stack.add(task_id)

            task = graph.get_task(task_id)
            if task:
                for dep_id in task.depends_on:
                    if dep_id not in visited:
                        if has_cycle(dep_id):
                            return True
                    elif dep_id in rec_stack:
                        issues.append(
                            {
                                "type": "circular_dependency",
                                "task_id": task_id,
                                "dependency_id": dep_id,
                                "message": f"Circular dependency detected: '{task_id}' -> '{dep_id}'",
                            }
                        )
                        return True

            rec_stack.remove(task_id)
            return False

        for task_id in graph.tasks:
            if task_id not in visited:
                has_cycle(task_id)

        # Check for orphaned parent references
        for task in graph.tasks.values():
            if task.parent_id and task.parent_id not in graph.tasks:
                issues.append(
                    {
                        "type": "missing_parent",
                        "task_id": task.id,
                        "parent_id": task.parent_id,
                        "message": f"Task '{task.title}' references non-existent parent '{task.parent_id}'",
                    }
                )

        return {"valid": len(issues) == 0, "issue_count": len(issues), "issues": issues}

    @staticmethod
    def _get_dependency_depth(
        graph: TaskGraph, task_id: str, visited: set[str] | None = None
    ) -> int:
        """Calculate the maximum dependency depth for a task."""
        if visited is None:
            visited = set()

        if task_id in visited:
            return 0  # Cycle detected

        visited.add(task_id)
        task = graph.get_task(task_id)

        if not task or not task.depends_on:
            return 0

        max_depth = 0
        for dep_id in task.depends_on:
            depth = DependencyService._get_dependency_depth(graph, dep_id, visited.copy())
            max_depth = max(max_depth, depth + 1)

        return max_depth

    @staticmethod
    def _save_graph(graph: TaskGraph) -> None:
        """Persist graph back to storage (DB if forced, else JSON)."""
        if Config.API_FORCE_DB:
            # Upsert tasks and dependencies to DB, then export snapshot
            for t in graph.tasks.values():
                try:
                    existing = _db.get_task(t.id)
                    if not existing:
                        _db.create_task(
                            {
                                "id": t.id,
                                "course": t.course,
                                "title": t.title,
                                "status": _status_model_to_db(t.status.value),
                                "parent_id": t.parent_id,
                                "due_at": t.due_date.isoformat()
                                if hasattr(t.due_date, "isoformat") and t.due_date
                                else None,
                                "weight": t.weight,
                                "category": t.category.value
                                if hasattr(t.category, "value")
                                else str(t.category),
                                "notes": t.description,
                                "depends_on": list(t.depends_on),
                            }
                        )
                    else:
                        _db.update_task_field(t.id, "status", _status_model_to_db(t.status.value))
                        # Ensure dependencies are present
                        if t.depends_on:
                            _db.add_deps(t.id, t.depends_on)
                except Exception:
                    pass
            # Export snapshot JSON for compatibility
            with contextlib.suppress(Exception):
                _db.export_snapshot_to_json(Config.TASKS_FILE)
            return
        # JSON fallback removed in v2 cleanup
        return
