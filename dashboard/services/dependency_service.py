#!/usr/bin/env python3
"""
Dependency resolution service for task management.
Handles complex task relationships and auto-unlocking.
"""

from datetime import datetime
from typing import Any

from dashboard.models import Task, TaskGraph, TaskStatus
from dashboard.services.task_service import TaskService


class DependencyService:
    """Service for managing task dependencies and relationships."""

    @staticmethod
    def build_task_graph() -> TaskGraph:
        """Build a complete task graph from stored tasks."""
        data = TaskService._load_tasks_data()
        graph = TaskGraph()

        for task_data in data.get("tasks", []):
            task = Task.from_dict(task_data)
            graph.add_task(task)

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
                blocker.title for dep_id in task.depends_on 
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
                    blocker.title for dep_id in task.depends_on 
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
        """Save the task graph back to storage."""
        tasks_data = [task.to_dict() for task in graph.tasks.values()]

        data = TaskService._load_tasks_data()
        data["tasks"] = tasks_data
        data["metadata"]["updated"] = datetime.now().isoformat()

        TaskService._save_tasks_data(data)
