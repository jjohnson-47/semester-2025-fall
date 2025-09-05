"""Test data builders for creating consistent test fixtures."""

from __future__ import annotations

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

from dashboard.db import Database, DatabaseConfig


class TaskBuilder:
    """Builder for creating test tasks."""
    
    def __init__(self, task_id: str = "TEST-001"):
        self.data = {
            "id": task_id,
            "title": f"Test Task {task_id}",
            "status": "todo",
            "priority": 5,
            "effort_hours": 2,
            "course": "MATH221",
            "type": "homework",
            "due_date": None,
            "dependencies": [],
            "checklist": [],
            "tags": [],
            "created_at": "2025-09-01T09:00:00Z",
            "updated_at": "2025-09-01T09:00:00Z",
            "chain_id": None,
            "chain_position": None,
            "phase": "todo",
            "score": 0.5,
            "now_score": 0.0,
            "downstream_unlocked": 0,
            "upstream_blocking": 0
        }
    
    def with_id(self, task_id: str) -> TaskBuilder:
        """Set the task ID."""
        self.data["id"] = task_id
        return self
    
    def with_title(self, title: str) -> TaskBuilder:
        """Set the task title."""
        self.data["title"] = title
        return self
    
    def with_status(self, status: str) -> TaskBuilder:
        """Set the task status."""
        self.data["status"] = status
        return self
    
    def with_priority(self, priority: int) -> TaskBuilder:
        """Set the task priority."""
        self.data["priority"] = priority
        return self
    
    def with_effort(self, hours: int) -> TaskBuilder:
        """Set the task effort in hours."""
        self.data["effort_hours"] = hours
        return self
    
    def with_course(self, course: str) -> TaskBuilder:
        """Set the task course."""
        self.data["course"] = course
        return self
    
    def with_type(self, task_type: str) -> TaskBuilder:
        """Set the task type."""
        self.data["type"] = task_type
        return self
    
    def with_due_date(self, due_date: str | datetime | None) -> TaskBuilder:
        """Set the task due date."""
        if isinstance(due_date, datetime):
            due_date = due_date.isoformat()
        self.data["due_date"] = due_date
        return self
    
    def with_dependencies(self, deps: list[str]) -> TaskBuilder:
        """Set the task dependencies."""
        self.data["dependencies"] = deps
        return self
    
    def with_chain(self, chain_id: str, position: int) -> TaskBuilder:
        """Set the task chain information."""
        self.data["chain_id"] = chain_id
        self.data["chain_position"] = position
        return self
    
    def with_phase(self, phase: str) -> TaskBuilder:
        """Set the task phase."""
        self.data["phase"] = phase
        return self
    
    def with_scores(
        self,
        score: float = 0.5,
        now_score: float = 0.0,
        downstream: int = 0,
        upstream: int = 0
    ) -> TaskBuilder:
        """Set the task scoring information."""
        self.data["score"] = score
        self.data["now_score"] = now_score
        self.data["downstream_unlocked"] = downstream
        self.data["upstream_blocking"] = upstream
        return self
    
    def with_checklist(self, items: list[dict[str, Any]]) -> TaskBuilder:
        """Set the task checklist."""
        self.data["checklist"] = items
        return self
    
    def build(self) -> dict[str, Any]:
        """Build the task dictionary."""
        return self.data.copy()


class TaskGraphBuilder:
    """Builder for creating test task graphs."""
    
    def __init__(self, seed: int = 42):
        self.tasks: list[dict[str, Any]] = []
        self.random = random.Random(seed)
        self.courses = ["MATH221", "MATH251", "STAT253"]
        self.types = ["homework", "exam", "project", "reading", "quiz"]
        self.phases = ["todo", "doing", "review", "done", "blocked"]
    
    def create_simple_chain(
        self,
        chain_id: str,
        length: int = 3,
        course: str = "MATH221"
    ) -> TaskGraphBuilder:
        """Create a simple linear dependency chain."""
        chain_tasks = []
        for i in range(length):
            task_id = f"{chain_id}-{i+1:02d}"
            task = (
                TaskBuilder(task_id)
                .with_title(f"{course} Chain Task {i+1}")
                .with_course(course)
                .with_chain(chain_id, i)
                .with_type(self.random.choice(self.types))
                .with_priority(self.random.randint(3, 8))
                .with_effort(self.random.randint(1, 4))
                .with_phase(self.phases[min(i, len(self.phases) - 1)])
            )
            
            # Add dependency on previous task
            if i > 0:
                task.with_dependencies([chain_tasks[-1]["id"]])
                task.with_scores(
                    score=0.5 + i * 0.1,
                    downstream=length - i - 1,
                    upstream=i
                )
            else:
                task.with_scores(
                    score=0.8,
                    downstream=length - 1,
                    upstream=0
                )
            
            chain_tasks.append(task.build())
        
        self.tasks.extend(chain_tasks)
        return self
    
    def create_standard_graph(self) -> TaskGraphBuilder:
        """Create a standard test graph with 8-12 tasks across 3 courses."""
        # Create 2 chains per course
        for i, course in enumerate(self.courses):
            self.create_simple_chain(f"{course}-CHAIN-A", 2, course)
            self.create_simple_chain(f"{course}-CHAIN-B", 2, course)
        
        # Add some standalone tasks
        for i in range(3):
            course = self.courses[i % len(self.courses)]
            task = (
                TaskBuilder(f"STANDALONE-{i+1:02d}")
                .with_title(f"{course} Standalone Task {i+1}")
                .with_course(course)
                .with_type(self.random.choice(self.types))
                .with_priority(self.random.randint(1, 10))
                .with_effort(self.random.randint(1, 6))
                .with_phase(self.random.choice(self.phases))
                .with_scores(score=0.3 + i * 0.1)
            )
            
            # Some tasks have due dates
            if i % 2 == 0:
                due = datetime(2025, 9, 15 + i * 2, 23, 59, 59)
                task.with_due_date(due)
            
            self.tasks.append(task.build())
        
        return self
    
    def create_complex_dag(self) -> TaskGraphBuilder:
        """Create a complex DAG with multiple paths and convergence."""
        # Create root task
        root = (
            TaskBuilder("DAG-ROOT")
            .with_title("Root Task")
            .with_course("MATH251")
            .with_priority(10)
            .with_scores(score=1.0, downstream=6)
        ).build()
        self.tasks.append(root)
        
        # Create two parallel branches
        branch_a = [
            TaskBuilder(f"DAG-A{i+1}")
            .with_title(f"Branch A Task {i+1}")
            .with_course("MATH251")
            .with_dependencies(["DAG-ROOT"] if i == 0 else [f"DAG-A{i}"])
            .with_scores(downstream=3 - i, upstream=i + 1)
            .build()
            for i in range(3)
        ]
        self.tasks.extend(branch_a)
        
        branch_b = [
            TaskBuilder(f"DAG-B{i+1}")
            .with_title(f"Branch B Task {i+1}")
            .with_course("STAT253")
            .with_dependencies(["DAG-ROOT"] if i == 0 else [f"DAG-B{i}"])
            .with_scores(downstream=2 - i, upstream=i + 1)
            .build()
            for i in range(2)
        ]
        self.tasks.extend(branch_b)
        
        # Create convergence point
        convergence = (
            TaskBuilder("DAG-CONVERGE")
            .with_title("Convergence Task")
            .with_course("MATH221")
            .with_dependencies(["DAG-A3", "DAG-B2"])
            .with_priority(8)
            .with_scores(upstream=5)
        ).build()
        self.tasks.append(convergence)
        
        return self
    
    def build(self) -> list[dict[str, Any]]:
        """Build the task graph."""
        return self.tasks.copy()
    
    def save_to_json(self, path: Path) -> None:
        """Save the task graph to a JSON file."""
        path.write_text(json.dumps(self.tasks, indent=2))
    
    def load_to_db(self, db: Database) -> None:
        """Load the task graph into a database."""
        # First create all tasks without dependencies
        for task in self.tasks:
            # Create base task with all fields
            task_data = {
                "id": task["id"],
                "title": task["title"],
                "status": task.get("status", "todo"),
                "priority": task.get("priority", 5),
                "effort_hours": task.get("effort_hours", 2),
                "course": task.get("course", "MATH221")
            }
            # Include additional fields in the creation
            for k, v in task.items():
                if k not in task_data and k != "dependencies":
                    task_data[k] = v
            
            db.create_task(task_data)
        
        # Then add dependencies (after all tasks exist)
        for task in self.tasks:
            for dep_id in task.get("dependencies", []):
                db.add_deps(task["id"], [dep_id])


def create_sample_course_data() -> dict[str, Any]:
    """Create sample course configuration data."""
    return {
        "courses": [
            {
                "code": "MATH221",
                "name": "Intermediate Algebra",
                "schedule": "MWF 8:00-8:50 AM",
                "color": "#0066cc"
            },
            {
                "code": "MATH251",
                "name": "Calculus I",
                "schedule": "MWF 9:00-9:50 AM",
                "color": "#006600"
            },
            {
                "code": "STAT253",
                "name": "Statistics I",
                "schedule": "TTh 10:00-11:15 AM",
                "color": "#cc6600"
            }
        ]
    }


def create_sample_now_queue() -> list[str]:
    """Create a sample now queue."""
    return [
        "MATH221-CHAIN-A-01",
        "MATH251-CHAIN-B-01",
        "STANDALONE-01",
        "DAG-ROOT"
    ]