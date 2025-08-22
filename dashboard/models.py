#!/usr/bin/env python3
"""
Data models for the task management dashboard with dependency graph support.

This module provides the core data structures for managing hierarchical tasks
with complex dependency relationships. It implements a directed acyclic graph
(DAG) for dependency management and supports automatic status updates based
on dependency resolution.

Key Components:
    - Task: Individual task with hierarchy and dependency support
    - TaskGraph: Container managing the dependency graph
    - TaskStatus, TaskPriority, TaskCategory: Enumerations for task properties

The models follow Python 3.13 best practices including:
    - Type hints for all parameters and return values
    - Dataclasses for automatic initialization and representation
    - Comprehensive validation and error handling
    - Efficient graph algorithms for dependency resolution

Example:
    Creating a task with dependencies::

        >>> from dashboard.models import Task, TaskGraph, TaskStatus
        >>>
        >>> # Create tasks
        >>> setup = Task(id="SETUP", course="MATH221", title="Setup course")
        >>> content = Task(
        ...     id="CONTENT",
        ...     course="MATH221",
        ...     title="Create content",
        ...     depends_on=["SETUP"]
        ... )
        >>>
        >>> # Build graph
        >>> graph = TaskGraph()
        >>> graph.add_task(setup)
        >>> graph.add_task(content)
        >>>
        >>> # Complete setup task
        >>> unblocked = graph.mark_completed("SETUP")
        >>> print(f"Unblocked {len(unblocked)} tasks")

Note:
    This module is designed to work with both JSON file storage and
    potential future database backends through the serialization methods.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any


class TaskStatus(Enum):
    """Task status enumeration."""

    BLOCKED = "blocked"
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    DEFERRED = "deferred"


class TaskPriority(Enum):
    """Task priority levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskCategory(Enum):
    """Task categories."""

    SETUP = "setup"
    CONTENT = "content"
    TECHNICAL = "technical"
    MATERIALS = "materials"
    ASSESSMENT = "assessment"
    COMMUNICATION = "communication"


@dataclass
class Task:
    """
    Task model with dependency and hierarchy support.
    Implements the dependency graph pattern for complex workflows.
    """

    id: str
    course: str
    title: str
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    category: TaskCategory = TaskCategory.SETUP

    # Hierarchy and dependencies
    parent_id: str | None = None
    depends_on: list[str] = field(default_factory=list)

    # Task details
    description: str | None = None
    assignee: str | None = None
    weight: int = 1
    due_date: date | None = None

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None

    # Computed fields (not stored)
    children: list["Task"] = field(default_factory=list, init=False, repr=False)
    blockers: list["Task"] = field(default_factory=list, init=False, repr=False)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert task to dictionary for JSON serialization.

        Converts all enum values to strings and datetime objects to ISO format
        strings for JSON compatibility. This method is used when persisting
        tasks to file storage or sending them via API responses.

        Returns:
            Dict[str, Any]: Dictionary representation with all fields serialized
                to JSON-compatible types. Includes all task fields except
                computed fields (children, blockers).

        Example:
            >>> task = Task(id="T1", course="MATH", title="Test")
            >>> data = task.to_dict()
            >>> json.dumps(data)  # Safe to serialize
        """
        return {
            "id": self.id,
            "course": self.course,
            "title": self.title,
            "status": self.status.value,
            "priority": self.priority.value,
            "category": self.category.value,
            "parent_id": self.parent_id,
            "depends_on": self.depends_on,
            "description": self.description,
            "assignee": self.assignee,
            "weight": self.weight,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Task":
        """
        Create a Task instance from a dictionary representation.

        Deserializes data from JSON-compatible dictionary format, converting
        string representations back to proper Python types (enums, dates, etc.).
        Handles missing fields gracefully by using defaults.

        Args:
            data: Dictionary containing task data, typically from JSON parsing.
                Expected keys match Task field names. String values for enums
                and ISO format strings for dates are automatically converted.

        Returns:
            Task: New Task instance with data from dictionary.

        Raises:
            ValueError: If enum values are invalid or date parsing fails.

        Example:
            >>> data = {'id': 'T1', 'course': 'MATH', 'title': 'Test',
            ...         'status': 'blocked', 'due_date': '2025-08-25'}
            >>> task = Task.from_dict(data)
            >>> assert task.status == TaskStatus.BLOCKED
            >>> assert task.due_date == date(2025, 8, 25)
        """
        # Convert string enums back to enum types
        if "status" in data and isinstance(data["status"], str):
            data["status"] = TaskStatus(data["status"])
        if "priority" in data and isinstance(data["priority"], str):
            data["priority"] = TaskPriority(data["priority"])
        if "category" in data and isinstance(data["category"], str):
            data["category"] = TaskCategory(data["category"])

        # Convert date strings to date objects
        if "due_date" in data and data["due_date"] and isinstance(data["due_date"], str):
            data["due_date"] = date.fromisoformat(data["due_date"])

        # Convert datetime strings to datetime objects
        for field_name in ["created_at", "updated_at", "completed_at"]:
            if field_name in data and data[field_name] and isinstance(data[field_name], str):
                data[field_name] = datetime.fromisoformat(data[field_name])

        # Ensure depends_on is a list
        if "depends_on" not in data:
            data["depends_on"] = []

        return cls(**data)

    def is_blocked(self) -> bool:
        """Check if task is blocked by dependencies."""
        return self.status == TaskStatus.BLOCKED

    def can_start(self, completed_tasks: set[str]) -> bool:
        """Check if all dependencies are completed."""
        if not self.depends_on:
            return True
        return all(dep_id in completed_tasks for dep_id in self.depends_on)

    def update_status_from_dependencies(self, completed_tasks: set[str]) -> bool:
        """
        Auto-update status based on dependencies.
        Returns True if status was changed.
        """
        if self.status == TaskStatus.DONE:
            return False

        can_start = self.can_start(completed_tasks)

        if not can_start and self.status != TaskStatus.BLOCKED:
            self.status = TaskStatus.BLOCKED
            return True
        elif can_start and self.status == TaskStatus.BLOCKED:
            self.status = TaskStatus.TODO
            return True

        return False


@dataclass
class TaskGraph:
    """
    Manages the dependency graph of tasks.
    Provides methods for topological sorting and dependency resolution.
    """

    tasks: dict[str, Task] = field(default_factory=dict)

    def add_task(self, task: Task) -> None:
        """Add a task to the graph."""
        self.tasks[task.id] = task
        self._update_relationships()

    def get_task(self, task_id: str) -> Task | None:
        """Get a task by ID."""
        return self.tasks.get(task_id)

    def get_children(self, parent_id: str) -> list[Task]:
        """Get all children of a parent task."""
        return [t for t in self.tasks.values() if t.parent_id == parent_id]

    def get_blockers(self, task_id: str) -> list[Task]:
        """Get all tasks that must be completed before this task."""
        task = self.tasks.get(task_id)
        if not task or not task.depends_on:
            return []
        return [self.tasks[dep_id] for dep_id in task.depends_on if dep_id in self.tasks]

    def get_blocked_by(self, task_id: str) -> list[Task]:
        """Get all tasks blocked by this task."""
        return [t for t in self.tasks.values() if task_id in t.depends_on]

    def mark_completed(self, task_id: str) -> list[Task]:
        """
        Mark a task as completed and return newly unblocked tasks.
        """
        task = self.tasks.get(task_id)
        if not task:
            return []

        task.status = TaskStatus.DONE
        task.completed_at = datetime.now()
        task.updated_at = datetime.now()

        # Find and unblock dependent tasks
        completed_ids = self._get_completed_task_ids()
        unblocked = []

        for blocked_task in self.get_blocked_by(task_id):
            if blocked_task.update_status_from_dependencies(completed_ids):
                unblocked.append(blocked_task)

        return unblocked

    def topological_sort(self) -> list[Task]:
        """
        Return tasks in dependency order using topological sort.
        Tasks with no dependencies come first.
        """
        from collections import deque

        # Build in-degree map: number of dependencies for each task
        in_degree = dict.fromkeys(self.tasks.keys(), 0)
        for task in self.tasks.values():
            for _dep_id in task.depends_on:
                # Edge is dep -> task, so increment task's in-degree
                if task.id in in_degree:
                    in_degree[task.id] += 1

        # Start with tasks that have no dependencies
        queue = deque([task_id for task_id, degree in in_degree.items() if degree == 0])
        sorted_tasks = []

        while queue:
            task_id = queue.popleft()
            sorted_tasks.append(self.tasks[task_id])

            # Reduce in-degree for dependent tasks
            for task in self.get_blocked_by(task_id):
                in_degree[task.id] -= 1
                if in_degree[task.id] == 0:
                    queue.append(task.id)

        return sorted_tasks

    def get_critical_path(self) -> list[Task]:
        """
        Find the critical path through the task graph.
        Returns the longest dependency chain by weight.
        """
        # This is a simplified version - full implementation would use
        # dynamic programming to find the actual critical path
        sorted_tasks = self.topological_sort()

        # Calculate cumulative weights
        weights: dict[str, float] = {}
        paths: dict[str, list[Task]] = {}

        for task in sorted_tasks:
            max_weight: float = 0.0
            predecessor = None

            for dep_id in task.depends_on:
                if dep_id in weights and weights[dep_id] > max_weight:
                    max_weight = weights[dep_id]
                    predecessor = dep_id

            weights[task.id] = max_weight + task.weight
            paths[task.id] = (paths.get(predecessor, []) if predecessor else []) + [task]

        # Find the path with maximum weight
        if not weights:
            return []

        max_task_id = max(weights, key=lambda k: weights[k])
        return paths.get(max_task_id, [])

    def _update_relationships(self) -> None:
        """Update the children and blockers relationships."""
        for task in self.tasks.values():
            task.children = self.get_children(task.id)
            task.blockers = self.get_blockers(task.id)

    def _get_completed_task_ids(self) -> set[str]:
        """Get set of completed task IDs."""
        return {t.id for t in self.tasks.values() if t.status == TaskStatus.DONE}
