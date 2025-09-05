"""Database helpers for testing."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any, Generator, Optional

import pytest

from dashboard.db import Database, DatabaseConfig


class DatabaseHelper:
    """Test database wrapper with convenience methods."""
    
    def __init__(self, db_path: Path | None = None):
        if db_path is None:
            self.temp_dir = tempfile.TemporaryDirectory()
            db_path = Path(self.temp_dir.name) / "test.db"
        else:
            self.temp_dir = None
        
        self.config = DatabaseConfig(db_path)
        self.db = Database(self.config)
        self.db.initialize()
    
    def seed_basic_tasks(self) -> None:
        """Seed the database with basic test tasks."""
        from .builders import TaskGraphBuilder
        
        builder = TaskGraphBuilder(seed=42)
        builder.create_standard_graph()
        builder.load_to_db(self.db)
    
    def seed_complex_dag(self) -> None:
        """Seed the database with a complex DAG."""
        from .builders import TaskGraphBuilder
        
        builder = TaskGraphBuilder(seed=42)
        builder.create_complex_dag()
        builder.load_to_db(self.db)
    
    def create_task_with_deps(
        self,
        task_id: str,
        deps: list[str],
        **kwargs: Any
    ) -> str:
        """Create a task with dependencies."""
        # Create the task
        task_data = {
            "id": task_id,
            "title": kwargs.get("title", f"Task {task_id}"),
            "status": kwargs.get("status", "todo"),
            "priority": kwargs.get("priority", 5),
            "effort_hours": kwargs.get("effort_hours", 2),
            "course": kwargs.get("course", "MATH221")
        }
        self.db.create_task(task_data)
        
        # Add dependencies
        for dep_id in deps:
            # Ensure dependency exists
            if not self.db.get_task(dep_id):
                dep_data = {
                    "id": dep_id,
                    "title": f"Dependency {dep_id}",
                    "status": "todo",
                    "priority": 5,
                    "effort_hours": 1,
                    "course": "MATH221"
                }
                self.db.create_task(dep_data)
            self.db.add_deps(task_id, [dep_id])
        
        return task_id
    
    def get_task_graph(self) -> dict[str, list[str]]:
        """Get the task dependency graph."""
        graph = {}
        tasks = self.db.list_tasks()
        
        for task in tasks:
            task_id = task["id"]
            # Get dependencies from deps table
            with self.db.connect() as conn:
                cursor = conn.execute(
                    "SELECT blocks_id FROM deps WHERE task_id = ?",
                    (task_id,)
                )
                deps = [row[0] for row in cursor]
            graph[task_id] = deps
        
        return graph
    
    def clear_all_tasks(self) -> None:
        """Clear all tasks from the database."""
        with self.db.connect() as conn:
            conn.execute("DELETE FROM deps")
            conn.execute("DELETE FROM tasks")
            conn.commit()
    
    def snapshot(self) -> dict[str, Any]:
        """Create a snapshot of the current database state."""
        return {
            "tasks": self.db.list_tasks(),
            "graph": self.get_task_graph(),
            "now_queue": self.db.get_now_queue()
        }
    
    def restore(self, snapshot: dict[str, Any]) -> None:
        """Restore database from a snapshot."""
        self.clear_all_tasks()
        
        # Restore tasks
        for task in snapshot.get("tasks", []):
            # Create task with all fields
            task_data = task.copy()
            # Ensure status is valid
            if task_data.get("status") == "pending":
                task_data["status"] = "todo"
            self.db.create_task(task_data)
        
        # Restore dependencies
        for task_id, deps in snapshot.get("graph", {}).items():
            for dep_id in deps:
                self.db.add_deps(task_id, [dep_id])
        
        # Restore now queue
        now_queue = snapshot.get("now_queue", [])
        if now_queue:
            self.db.set_now_queue(now_queue)
    
    def cleanup(self) -> None:
        """Clean up the test database."""
        if self.temp_dir:
            self.temp_dir.cleanup()
    
    def __enter__(self) -> DatabaseHelper:
        """Context manager entry."""
        return self
    
    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.cleanup()


@pytest.fixture
def test_db(tmp_path: Path) -> Generator[DatabaseHelper, None, None]:
    """Fixture providing a test database."""
    db = DatabaseHelper(tmp_path / "test.db")
    yield db
    db.cleanup()


@pytest.fixture
def seeded_db(tmp_path: Path) -> Generator[DatabaseHelper, None, None]:
    """Fixture providing a test database with seed data."""
    db = DatabaseHelper(tmp_path / "test.db")
    db.seed_basic_tasks()
    yield db
    db.cleanup()


def create_temp_db(seed_data: bool = False) -> DatabaseHelper:
    """Create a temporary test database."""
    db = DatabaseHelper()
    if seed_data:
        db.seed_basic_tasks()
    return db


class DatabaseSnapshot:
    """Helper for database state management in tests."""
    
    def __init__(self, db: DatabaseHelper):
        self.db = db
        self.snapshots: dict[str, dict[str, Any]] = {}
    
    def capture(self, name: str = "default") -> None:
        """Capture current database state."""
        self.snapshots[name] = self.db.snapshot()
    
    def restore(self, name: str = "default") -> None:
        """Restore database to a captured state."""
        if name not in self.snapshots:
            raise ValueError(f"No snapshot named '{name}'")
        self.db.restore(self.snapshots[name])
    
    def assert_unchanged(self, name: str = "default") -> None:
        """Assert that database state hasn't changed since snapshot."""
        if name not in self.snapshots:
            raise ValueError(f"No snapshot named '{name}'")
        
        current = self.db.snapshot()
        expected = self.snapshots[name]
        
        # Compare tasks
        assert len(current["tasks"]) == len(expected["tasks"]), \
            "Task count mismatch"
        
        current_tasks = {t["id"]: t for t in current["tasks"]}
        expected_tasks = {t["id"]: t for t in expected["tasks"]}
        
        assert set(current_tasks.keys()) == set(expected_tasks.keys()), \
            "Task IDs mismatch"
        
        for task_id in expected_tasks:
            assert current_tasks[task_id] == expected_tasks[task_id], \
                f"Task {task_id} differs"
        
        # Compare graph
        assert current["graph"] == expected["graph"], \
            "Dependency graph mismatch"
        
        # Compare now queue
        assert current["now_queue"] == expected["now_queue"], \
            "Now queue mismatch"