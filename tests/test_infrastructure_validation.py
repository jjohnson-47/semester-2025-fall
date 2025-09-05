"""Validation tests for Track 0 infrastructure.

These tests ensure all fixtures and helpers are working correctly.
"""

import asyncio
from datetime import datetime, timezone
from pathlib import Path

import pytest

from tests.helpers.builders import TaskBuilder, TaskGraphBuilder
from tests.helpers.clocks import FakeClock, TimeTravel
from tests.helpers.db import DatabaseHelper, DatabaseSnapshot
from tests.helpers.fake_process import FakeProcess, FakeProcessFactory


@pytest.mark.unit
class TestFakeProcess:
    """Test the fake process infrastructure."""
    
    def test_fake_process_basic(self):
        """Test basic fake process functionality."""
        process = FakeProcess(
            stdout="Hello",
            stderr="Warning",
            returncode=0
        )
        
        # Synchronous test of async method
        loop = asyncio.new_event_loop()
        stdout, stderr = loop.run_until_complete(process.communicate())
        loop.close()
        
        assert stdout == b"Hello"
        assert stderr == b"Warning"
        assert process._communicate_called
    
    def test_fake_process_factory(self):
        """Test the process factory."""
        factory = FakeProcessFactory()
        
        # Register a command
        factory.register(
            "echo test",
            stdout="test output",
            returncode=0
        )
        
        # Create subprocess
        loop = asyncio.new_event_loop()
        process = loop.run_until_complete(
            factory.create_subprocess_shell("echo test")
        )
        stdout, stderr = loop.run_until_complete(process.communicate())
        loop.close()
        
        assert stdout == b"test output"
        assert factory.call_count == 1
        factory.assert_called_with("echo test")


@pytest.mark.unit
class TestClocks:
    """Test time control utilities."""
    
    def test_fake_clock_basic(self):
        """Test basic clock operations."""
        clock = FakeClock()
        
        # Check initial time
        assert clock.now() == datetime(2025, 9, 1, 9, 0, 1, tzinfo=timezone.utc)
        
        # Freeze and check
        clock.freeze()
        time1 = clock.now()
        time2 = clock.now()
        assert time1 == time2
        
        # Unfreeze and advance
        clock.unfreeze()
        clock.tick(hours=2)
        assert clock.now().hour == 11
    
    def test_time_travel(self):
        """Test time travel helper."""
        clock = FakeClock()
        clock.freeze()  # Freeze to prevent auto-advance
        travel = TimeTravel(clock)
        
        # Set checkpoint
        travel.checkpoint("start")
        
        # Advance time
        clock.tick(minutes=30)
        
        # Check elapsed
        elapsed = travel.elapsed_since("start")
        assert elapsed.total_seconds() == 1800  # 30 minutes exactly


@pytest.mark.unit
class TestBuilders:
    """Test data builders."""
    
    def test_task_builder(self):
        """Test task builder."""
        task = (
            TaskBuilder("TEST-001")
            .with_title("Test Task")
            .with_course("MATH221")
            .with_priority(8)
            .with_dependencies(["DEP-001", "DEP-002"])
            .build()
        )
        
        assert task["id"] == "TEST-001"
        assert task["title"] == "Test Task"
        assert task["course"] == "MATH221"
        assert task["priority"] == 8
        assert len(task["dependencies"]) == 2
    
    def test_task_graph_builder(self):
        """Test task graph builder."""
        builder = TaskGraphBuilder(seed=42)
        builder.create_simple_chain("CHAIN", 3, "MATH251")
        tasks = builder.build()
        
        assert len(tasks) == 3
        assert tasks[0]["id"] == "CHAIN-01"
        assert tasks[1]["dependencies"] == ["CHAIN-01"]
        assert tasks[2]["dependencies"] == ["CHAIN-02"]


@pytest.mark.unit
class TestDatabaseHelpers:
    """Test database helpers."""
    
    def test_test_database(self, tmp_path):
        """Test DatabaseHelper wrapper."""
        db = DatabaseHelper(tmp_path / "test.db")
        
        # Seed basic tasks
        db.seed_basic_tasks()
        
        # Check tasks were created
        tasks = db.db.list_tasks()
        assert len(tasks) > 0
        
        # Test snapshot
        snapshot = db.snapshot()
        assert "tasks" in snapshot
        assert "graph" in snapshot
        
        # Clean up
        db.cleanup()
    
    def test_database_snapshot(self, tmp_path):
        """Test database snapshot functionality."""
        db = DatabaseHelper(tmp_path / "test.db")
        snap = DatabaseSnapshot(db)
        
        # Seed and capture
        db.seed_basic_tasks()
        snap.capture("initial")
        
        # Modify
        db.clear_all_tasks()
        
        # Restore
        snap.restore("initial")
        
        # Verify restored
        tasks = db.db.list_tasks()
        assert len(tasks) > 0
        
        db.cleanup()


@pytest.mark.unit
class TestFixtures:
    """Test pytest fixtures."""
    
    def test_frozen_time_fixture(self, frozen_time):
        """Test frozen time fixture."""
        now1 = datetime.now(timezone.utc)
        now2 = datetime.now(timezone.utc)
        
        assert now1 == now2
        assert now1.year == 2025
        assert now1.month == 9
        assert now1.day == 1
    
    def test_tmp_state_dir_fixture(self, tmp_state_dir):
        """Test temp state directory fixture."""
        assert tmp_state_dir.exists()
        assert (tmp_state_dir / "snapshots").exists()
        assert (tmp_state_dir / "logs").exists()
        assert (tmp_state_dir / "tasks.json").exists()
        assert (tmp_state_dir / "now_queue.json").exists()
        assert (tmp_state_dir / "courses.json").exists()
    
    def test_repo_fixture(self, repo):
        """Test repository fixture."""
        assert repo.db is not None
        
        # Create a task using dict format
        task_data = {
            "id": "TEST-001",
            "title": "Test Task",
            "status": "todo",
            "priority": 5,
            "effort_hours": 2,
            "course": "MATH221"
        }
        repo.db.create_task(task_data)
        
        # Verify it was created
        task = repo.db.get_task("TEST-001")
        assert task is not None
        assert task["title"] == "Test Task"
    
    def test_seeded_repo_fixture(self, seeded_repo):
        """Test seeded repository fixture."""
        tasks = seeded_repo.db.list_tasks()
        assert len(tasks) > 0
        
        # Check graph structure
        graph = seeded_repo.get_task_graph()
        assert len(graph) > 0
    
    def test_event_store_inmemory_fixture(self, event_store_inmemory):
        """Test in-memory event store fixture."""
        loop = asyncio.new_event_loop()
        
        # Append event
        loop.run_until_complete(
            event_store_inmemory.append("test-stream", {"type": "created"})
        )
        
        # Load events
        events = loop.run_until_complete(
            event_store_inmemory.load("test-stream")
        )
        
        loop.close()
        
        assert len(events) == 1
        assert events[0]["type"] == "created"
    
    def test_mock_subprocess_fixture(self, mock_subprocess):
        """Test subprocess mocking fixture."""
        mock_subprocess.register(
            "custom command",
            stdout="Custom output",
            returncode=42
        )
        
        loop = asyncio.new_event_loop()
        
        # The fixture patches asyncio.create_subprocess_shell
        process = loop.run_until_complete(
            asyncio.create_subprocess_shell("custom command")
        )
        stdout, stderr = loop.run_until_complete(process.communicate())
        
        loop.close()
        
        assert stdout == b"Custom output"
        assert process.returncode == 42


@pytest.mark.integration
class TestIntegrationSetup:
    """Test that integration between components works."""
    
    def test_database_with_builders(self, repo):
        """Test database integration with builders."""
        builder = TaskGraphBuilder()
        builder.create_standard_graph()
        builder.load_to_db(repo.db)
        
        tasks = repo.db.list_tasks()
        assert len(tasks) == len(builder.tasks)
    
    @pytest.mark.asyncio
    async def test_async_process_mock(self, mock_subprocess):
        """Test async process mocking."""
        mock_subprocess.register(
            "long command",
            stdout="Done",
            delay=0.1
        )
        
        process = await asyncio.create_subprocess_shell("long command")
        stdout, stderr = await process.communicate()
        
        assert stdout == b"Done"