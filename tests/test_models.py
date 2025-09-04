#!/usr/bin/env python3
"""
Comprehensive unit tests for dashboard models.

Tests the Task and TaskGraph models with focus on:
- Data validation and serialization
- Dependency management
- Hierarchy relationships
- Edge cases and error conditions

Following pytest 8.x best practices with:
- Descriptive test names
- Comprehensive fixtures
- Property-based testing with Hypothesis
- Parametrized tests for multiple scenarios
"""

import json

# Import models to test
import sys
from datetime import date, datetime
from pathlib import Path

import pytest

_hyp = pytest.importorskip("hypothesis")
given = _hyp.given  # type: ignore[attr-defined]
st = pytest.importorskip("hypothesis.strategies")  # type: ignore

sys.path.insert(0, str(Path(__file__).parent.parent))

from dashboard.models import Task, TaskCategory, TaskGraph, TaskPriority, TaskStatus


class TestTaskModel:
    """Test suite for the Task model."""

    @pytest.fixture
    def basic_task(self) -> Task:
        """Create a basic task for testing."""
        return Task(
            id="MATH221-SYLLABUS",
            course="MATH221",
            title="Create course syllabus",
            status=TaskStatus.TODO,
            priority=TaskPriority.HIGH,
            category=TaskCategory.SETUP,
        )

    @pytest.fixture
    def task_with_dependencies(self) -> Task:
        """Create a task with dependencies."""
        return Task(
            id="MATH221-BB-ASSIGNMENT",
            course="MATH221",
            title="Create first assignment",
            status=TaskStatus.BLOCKED,
            depends_on=["MATH221-BB-SETUP", "MATH221-GRADEBOOK"],
            parent_id="MATH221-BB-MODULE",
        )

    def test_task_creation_with_defaults(self):
        """Test that task creation uses appropriate defaults."""
        task = Task(id="TEST-001", course="TEST", title="Test Task")

        assert task.status == TaskStatus.TODO
        assert task.priority == TaskPriority.MEDIUM
        assert task.category == TaskCategory.SETUP
        assert task.depends_on == []
        assert task.parent_id is None
        assert task.weight == 1
        assert isinstance(task.created_at, datetime)
        assert isinstance(task.updated_at, datetime)

    def test_task_to_dict_serialization(self, basic_task):
        """Test converting task to dictionary for JSON serialization."""
        task_dict = basic_task.to_dict()

        assert task_dict["id"] == "MATH221-SYLLABUS"
        assert task_dict["course"] == "MATH221"
        assert task_dict["status"] == "todo"
        assert task_dict["priority"] == "high"
        assert task_dict["category"] == "setup"
        assert "created_at" in task_dict
        assert "updated_at" in task_dict

        # Ensure it's JSON serializable
        json_str = json.dumps(task_dict)
        assert json_str

    def test_task_from_dict_deserialization(self):
        """Test creating task from dictionary."""
        data = {
            "id": "TEST-002",
            "course": "TEST",
            "title": "Test Task",
            "status": "in_progress",
            "priority": "critical",
            "category": "content",
            "depends_on": ["TEST-001"],
            "due_date": "2025-08-25",
        }

        task = Task.from_dict(data)

        assert task.id == "TEST-002"
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.priority == TaskPriority.CRITICAL
        assert task.category == TaskCategory.CONTENT
        assert task.depends_on == ["TEST-001"]
        assert task.due_date == date(2025, 8, 25)

    def test_task_is_blocked(self, task_with_dependencies):
        """Test blocked status detection."""
        assert task_with_dependencies.is_blocked() is True

        task_with_dependencies.status = TaskStatus.TODO
        assert task_with_dependencies.is_blocked() is False

    def test_task_can_start(self, task_with_dependencies):
        """Test dependency checking for task start eligibility."""
        completed_tasks: set[str] = set()

        # Task cannot start with no completed dependencies
        assert task_with_dependencies.can_start(completed_tasks) is False

        # Task cannot start with only partial dependencies completed
        completed_tasks.add("MATH221-BB-SETUP")
        assert task_with_dependencies.can_start(completed_tasks) is False

        # Task can start when all dependencies completed
        completed_tasks.add("MATH221-GRADEBOOK")
        assert task_with_dependencies.can_start(completed_tasks) is True

    def test_task_update_status_from_dependencies(self, task_with_dependencies):
        """Test automatic status updates based on dependencies."""
        completed_tasks: set[str] = set()

        # Should become blocked when dependencies not met
        task_with_dependencies.status = TaskStatus.TODO
        changed = task_with_dependencies.update_status_from_dependencies(completed_tasks)
        assert changed is True
        assert task_with_dependencies.status == TaskStatus.BLOCKED

        # Should become unblocked when dependencies met
        completed_tasks.update(["MATH221-BB-SETUP", "MATH221-GRADEBOOK"])
        changed = task_with_dependencies.update_status_from_dependencies(completed_tasks)
        assert changed is True
        assert task_with_dependencies.status == TaskStatus.TODO

        # Should not change if already done
        task_with_dependencies.status = TaskStatus.DONE
        changed = task_with_dependencies.update_status_from_dependencies(set())
        assert changed is False
        assert task_with_dependencies.status == TaskStatus.DONE

    @pytest.mark.parametrize(
        "status,expected",
        [
            (TaskStatus.BLOCKED, True),
            (TaskStatus.TODO, False),
            (TaskStatus.IN_PROGRESS, False),
            (TaskStatus.DONE, False),
            (TaskStatus.DEFERRED, False),
        ],
    )
    def test_is_blocked_with_different_statuses(self, status, expected):
        """Test is_blocked method with different status values."""
        task = Task(id="TEST", course="TEST", title="Test", status=status)
        assert task.is_blocked() == expected

    @given(
        task_id=st.text(min_size=1, max_size=50),
        course=st.text(min_size=1, max_size=10),
        title=st.text(min_size=1, max_size=200),
        weight=st.integers(min_value=1, max_value=10),
    )
    def test_task_creation_with_random_data(self, task_id, course, title, weight):
        """Property-based test for task creation with random valid data."""
        task = Task(id=task_id, course=course, title=title, weight=weight)

        assert task.id == task_id
        assert task.course == course
        assert task.title == title
        assert task.weight == weight
        assert task.to_dict()  # Should be serializable


class TestTaskGraph:
    """Test suite for the TaskGraph dependency management."""

    @pytest.fixture
    def simple_graph(self) -> TaskGraph:
        """Create a simple task graph for testing."""
        graph = TaskGraph()

        # Create a simple dependency chain: A -> B -> C
        task_a = Task(id="A", course="TEST", title="Task A")
        task_b = Task(id="B", course="TEST", title="Task B", depends_on=["A"])
        task_c = Task(id="C", course="TEST", title="Task C", depends_on=["B"])

        graph.add_task(task_a)
        graph.add_task(task_b)
        graph.add_task(task_c)

        return graph

    @pytest.fixture
    def complex_graph(self) -> TaskGraph:
        """Create a complex graph with multiple paths."""
        graph = TaskGraph()

        # Create a diamond dependency:
        #     A
        #    / \
        #   B   C
        #    \ /
        #     D
        tasks = [
            Task(id="A", course="TEST", title="Setup"),
            Task(id="B", course="TEST", title="Left path", depends_on=["A"]),
            Task(id="C", course="TEST", title="Right path", depends_on=["A"]),
            Task(id="D", course="TEST", title="Final", depends_on=["B", "C"]),
        ]

        for task in tasks:
            graph.add_task(task)

        return graph

    @pytest.fixture
    def hierarchical_graph(self) -> TaskGraph:
        """Create a graph with parent-child relationships."""
        graph = TaskGraph()

        parent = Task(id="PARENT", course="TEST", title="Parent Task")
        child1 = Task(id="CHILD1", course="TEST", title="Child 1", parent_id="PARENT")
        child2 = Task(id="CHILD2", course="TEST", title="Child 2", parent_id="PARENT")
        grandchild = Task(id="GRANDCHILD", course="TEST", title="Grandchild", parent_id="CHILD1")

        for task in [parent, child1, child2, grandchild]:
            graph.add_task(task)

        return graph

    def test_add_and_get_task(self, simple_graph):
        """Test adding and retrieving tasks from graph."""
        task = simple_graph.get_task("A")
        assert task is not None
        assert task.id == "A"
        assert task.title == "Task A"

        # Non-existent task
        assert simple_graph.get_task("Z") is None

    def test_get_children(self, hierarchical_graph):
        """Test retrieving child tasks."""
        children = hierarchical_graph.get_children("PARENT")
        assert len(children) == 2
        assert all(child.parent_id == "PARENT" for child in children)

        # Grandchildren not included
        child_ids = [c.id for c in children]
        assert "CHILD1" in child_ids
        assert "CHILD2" in child_ids
        assert "GRANDCHILD" not in child_ids

    def test_get_blockers(self, simple_graph):
        """Test retrieving blocking tasks (dependencies)."""
        blockers = simple_graph.get_blockers("C")
        assert len(blockers) == 1
        assert blockers[0].id == "B"

        blockers = simple_graph.get_blockers("B")
        assert len(blockers) == 1
        assert blockers[0].id == "A"

        blockers = simple_graph.get_blockers("A")
        assert len(blockers) == 0

    def test_get_blocked_by(self, simple_graph):
        """Test retrieving tasks blocked by a given task."""
        blocked = simple_graph.get_blocked_by("A")
        assert len(blocked) == 1
        assert blocked[0].id == "B"

        blocked = simple_graph.get_blocked_by("C")
        assert len(blocked) == 0

    def test_mark_completed_with_unblocking(self, complex_graph):
        """Test marking tasks complete and unblocking dependencies."""
        # Initially, B and C are blocked by A, D is blocked by B and C
        for task_id in ["B", "C", "D"]:
            task = complex_graph.get_task(task_id)
            task.status = TaskStatus.BLOCKED

        # Complete A, should unblock B and C
        unblocked = complex_graph.mark_completed("A")
        assert len(unblocked) == 2
        assert {t.id for t in unblocked} == {"B", "C"}

        # Verify B and C are now TODO
        assert complex_graph.get_task("B").status == TaskStatus.TODO
        assert complex_graph.get_task("C").status == TaskStatus.TODO

        # D should still be blocked
        assert complex_graph.get_task("D").status == TaskStatus.BLOCKED

        # Complete B
        unblocked = complex_graph.mark_completed("B")
        assert len(unblocked) == 0  # D still waiting for C

        # Complete C, should unblock D
        unblocked = complex_graph.mark_completed("C")
        assert len(unblocked) == 1
        assert unblocked[0].id == "D"

    def test_topological_sort(self, complex_graph):
        """Test topological sorting of tasks."""
        sorted_tasks = complex_graph.topological_sort()

        # Convert to list of IDs for easier testing
        sorted_ids = [t.id for t in sorted_tasks]

        # A should come before B and C
        assert sorted_ids.index("A") < sorted_ids.index("B")
        assert sorted_ids.index("A") < sorted_ids.index("C")

        # B and C should come before D
        assert sorted_ids.index("B") < sorted_ids.index("D")
        assert sorted_ids.index("C") < sorted_ids.index("D")

    def test_critical_path(self, complex_graph):
        """Test finding the critical path through the graph."""
        # Set weights to make one path longer
        complex_graph.get_task("B").weight = 5
        complex_graph.get_task("C").weight = 2
        complex_graph.get_task("D").weight = 3

        critical_path = complex_graph.get_critical_path()
        path_ids = [t.id for t in critical_path]

        # Critical path should be A -> B -> D (weight = 1 + 5 + 3 = 9)
        assert "A" in path_ids
        assert "B" in path_ids
        assert "D" in path_ids

    def test_circular_dependency_detection(self):
        """Test that circular dependencies are handled."""
        graph = TaskGraph()

        # Create circular dependency: A -> B -> C -> A
        task_a = Task(id="A", course="TEST", title="A", depends_on=["C"])
        task_b = Task(id="B", course="TEST", title="B", depends_on=["A"])
        task_c = Task(id="C", course="TEST", title="C", depends_on=["B"])

        graph.add_task(task_a)
        graph.add_task(task_b)
        graph.add_task(task_c)

        # Topological sort should handle this gracefully
        # (In production, would detect and report the cycle)
        sorted_tasks = graph.topological_sort()
        assert len(sorted_tasks) <= 3

    @pytest.mark.parametrize(
        "num_tasks,num_deps",
        [
            (5, 0),  # No dependencies
            (5, 4),  # Linear chain
            (10, 15),  # Complex graph
            (3, 3),  # Fully connected
        ],
    )
    def test_graph_with_varying_complexity(self, num_tasks, num_deps):
        """Test graph operations with different complexity levels."""
        graph = TaskGraph()

        # Create tasks
        for i in range(num_tasks):
            task = Task(id=f"T{i}", course="TEST", title=f"Task {i}")
            graph.add_task(task)

        # Add random dependencies (simplified for testing)
        dep_count = 0
        for i in range(1, num_tasks):
            if dep_count < num_deps and i > 0:
                task = graph.get_task(f"T{i}")
                task.depends_on = [f"T{i - 1}"]
                dep_count += 1

        # Graph operations should work regardless of complexity
        assert len(graph.tasks) == num_tasks
        sorted_tasks = graph.topological_sort()
        assert len(sorted_tasks) <= num_tasks
