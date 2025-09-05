"""Pytest configuration for test discovery and import path.

Ensures the repository root is on sys.path so tests can import
project modules like `scripts.validate_json` reliably across environments.
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from freezegun import freeze_time

from dashboard.db import Database, DatabaseConfig
from tests.helpers.builders import TaskGraphBuilder, create_sample_course_data
from tests.helpers.clocks import STANDARD_TEST_TIME, FakeClock
from tests.helpers.db import DatabaseHelper
from tests.helpers.fake_process import FakeProcessFactory


def _ensure_repo_root_on_path() -> None:
    """Prepend the repository root to sys.path if missing.

    This makes `import scripts...` work regardless of how pytest computes
    its rootdir when invoked (e.g., `pytest`, `pytest tests/`).
    """

    repo_root = Path(__file__).resolve().parents[1]
    repo_root_str = str(repo_root)
    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)


_ensure_repo_root_on_path()


# Configure pytest markers
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "property: Property-based tests")
    config.addinivalue_line("markers", "slow: Slow tests")
    config.addinivalue_line("markers", "solver: CP-SAT solver tests")
    config.addinivalue_line("markers", "flaky: Known flaky tests")


# Time fixtures
@pytest.fixture
def frozen_time():
    """Freeze time at standard test time."""
    with freeze_time(STANDARD_TEST_TIME) as frozen:
        yield frozen


@pytest.fixture
def test_clock():
    """Provide a controllable test clock."""
    clock = FakeClock(STANDARD_TEST_TIME)
    return clock


# Directory fixtures
@pytest.fixture
def tmp_state_dir(tmp_path: Path) -> Path:
    """Provide an isolated temp directory for state files."""
    state_dir = tmp_path / "state"
    state_dir.mkdir(exist_ok=True)
    
    # Create standard subdirectories
    (state_dir / "snapshots").mkdir(exist_ok=True)
    (state_dir / "logs").mkdir(exist_ok=True)
    
    # Create default state files
    (state_dir / "tasks.json").write_text("[]")
    (state_dir / "now_queue.json").write_text("[]")
    (state_dir / "courses.json").write_text(
        json.dumps(create_sample_course_data(), indent=2)
    )
    
    return state_dir


# Database fixtures
@pytest.fixture
def repo(tmp_path: Path) -> Generator[DatabaseHelper, None, None]:
    """Provide an initialized test database."""
    db = DatabaseHelper(tmp_path / "test.db")
    yield db
    db.cleanup()


@pytest.fixture
def seeded_repo(tmp_path: Path) -> Generator[DatabaseHelper, None, None]:
    """Provide a test database with seed data."""
    db = DatabaseHelper(tmp_path / "test.db")
    db.seed_basic_tasks()
    yield db
    db.cleanup()


@pytest.fixture
def complex_dag_repo(tmp_path: Path) -> Generator[DatabaseHelper, None, None]:
    """Provide a test database with complex DAG."""
    db = DatabaseHelper(tmp_path / "test.db")
    db.seed_complex_dag()
    yield db
    db.cleanup()


# Process fixtures
@pytest.fixture
def fake_process_factory() -> FakeProcessFactory:
    """Provide a fake process factory for mocking subprocesses."""
    factory = FakeProcessFactory()
    
    # Set common defaults
    factory.set_default(
        stdout="Command executed successfully",
        stderr="",
        returncode=0
    )
    
    # Register common commands
    factory.register(
        "git status",
        stdout="On branch main\nnothing to commit, working tree clean",
        returncode=0
    )
    
    factory.register(
        "make",
        stdout="Build completed successfully",
        returncode=0
    )
    
    factory.register(
        "pytest",
        stdout="===== 42 passed in 1.23s =====",
        returncode=0
    )
    
    return factory


@pytest.fixture
def mock_subprocess(fake_process_factory: FakeProcessFactory):
    """Mock asyncio.create_subprocess_shell."""
    with patch("asyncio.create_subprocess_shell", fake_process_factory.create_subprocess_shell):
        yield fake_process_factory


# Event store fixtures
class InMemoryEventStore:
    """Simple in-memory event store for testing."""
    
    def __init__(self):
        self.events: list[dict[str, Any]] = []
        self.snapshots: dict[str, Any] = {}
    
    async def append(self, stream_id: str, event: dict[str, Any]) -> None:
        """Append an event to the stream."""
        self.events.append({
            "stream_id": stream_id,
            "event": event,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    async def load(self, stream_id: str) -> list[dict[str, Any]]:
        """Load events for a stream."""
        return [
            e["event"] for e in self.events
            if e["stream_id"] == stream_id
        ]
    
    async def snapshot(self, stream_id: str, state: Any) -> None:
        """Save a snapshot."""
        self.snapshots[stream_id] = state
    
    async def load_snapshot(self, stream_id: str) -> Any:
        """Load a snapshot."""
        return self.snapshots.get(stream_id)
    
    def clear(self) -> None:
        """Clear all events and snapshots."""
        self.events.clear()
        self.snapshots.clear()


@pytest.fixture
def event_store_inmemory() -> InMemoryEventStore:
    """Provide an in-memory event store."""
    return InMemoryEventStore()


@pytest.fixture
def event_store_sqlite(tmp_path: Path) -> Database:
    """Provide a SQLite-backed event store."""
    db_path = tmp_path / "events.db"
    config = DatabaseConfig(db_path)
    db = Database(config)
    db.initialize()
    
    # Add events table if not exists
    with db.get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stream_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                event_data TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_stream_id ON events(stream_id)
        """)
        conn.commit()
    
    return db


# Logging fixtures
@pytest.fixture
def caplog_debug(caplog):
    """Capture DEBUG level logs."""
    caplog.set_level(logging.DEBUG)
    return caplog


# Async fixtures
@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Mock fixtures for common services
@pytest.fixture
def mock_prioritization_service():
    """Mock prioritization service."""
    service = MagicMock()
    service.refresh_now_queue = AsyncMock(return_value=[])
    service.explain = MagicMock(return_value={"score": 0.5, "factors": {}})
    service.compute_scores = AsyncMock(return_value={})
    return service


@pytest.fixture
def mock_dependency_service():
    """Mock dependency service."""
    service = MagicMock()
    service.build_task_graph = MagicMock(return_value={})
    service.get_blocking_tasks = MagicMock(return_value=[])
    service.get_blocked_tasks = MagicMock(return_value=[])
    return service


@pytest.fixture
def mock_deploy_api():
    """Mock deployment API."""
    api = MagicMock()
    api.run_command = AsyncMock(return_value=(0, "Success", ""))
    api.build_site = AsyncMock(return_value=True)
    api.deploy_worker = AsyncMock(return_value=True)
    api.verify_deployment = AsyncMock(return_value=True)
    return api


# Flask app fixture
@pytest.fixture
def app():
    """Create Flask test app."""
    from dashboard.app import create_app
    
    app = create_app()
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    
    return app


@pytest.fixture
def client(app):
    """Create Flask test client."""
    return app.test_client()


# Note: Removed autouse cleanup fixture that was deleting pytest temp directories
# pytest manages its own temp directories properly
