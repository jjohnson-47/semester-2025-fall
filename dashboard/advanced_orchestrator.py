#!/usr/bin/env python3
"""Advanced Orchestration System with Modern Patterns.

Implements cutting-edge orchestration paradigms:
- Event-driven architecture with event sourcing
- State machines for workflow management
- Reactive streams for real-time processing
- SAGA pattern for distributed transactions
- Circuit breakers for resilience
- Backpressure handling for flow control
"""

import asyncio
import hashlib
import json
import logging
import time
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Event types in the system."""

    TASK_CREATED = auto()
    TASK_STARTED = auto()
    TASK_COMPLETED = auto()
    TASK_FAILED = auto()
    TASK_BLOCKED = auto()
    TASK_UNBLOCKED = auto()
    AGENT_REGISTERED = auto()
    AGENT_ASSIGNED = auto()
    AGENT_COMPLETED = auto()
    WORKFLOW_STARTED = auto()
    WORKFLOW_COMPLETED = auto()
    DEPENDENCY_RESOLVED = auto()
    RESOURCE_AVAILABLE = auto()
    DEADLINE_APPROACHING = auto()
    SYSTEM_ERROR = auto()
    OPTIMIZATION_SUGGESTED = auto()


@dataclass
class Event:
    """Immutable event in the system."""

    id: str
    type: EventType
    timestamp: datetime
    payload: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type.name,
            "timestamp": self.timestamp.isoformat(),
            "payload": self.payload,
            "metadata": self.metadata,
        }


class EventStore:
    """Event store with event sourcing capabilities."""

    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.mkdir(exist_ok=True)
        self.events_file = self.storage_path / "events.jsonl"
        self.snapshots_dir = self.storage_path / "snapshots"
        self.snapshots_dir.mkdir(exist_ok=True)

        self.events: list[Event] = []
        self.subscribers: dict[EventType, list[Callable]] = defaultdict(list)
        self._load_events()

    def _load_events(self):
        """Load events from persistent storage."""
        if self.events_file.exists():
            with open(self.events_file) as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        event = Event(
                            id=data["id"],
                            type=EventType[data["type"]],
                            timestamp=datetime.fromisoformat(data["timestamp"]),
                            payload=data["payload"],
                            metadata=data.get("metadata", {}),
                        )
                        self.events.append(event)

    async def append(self, event: Event):
        """Append event to store and notify subscribers."""
        self.events.append(event)

        # Persist to disk
        with open(self.events_file, "a") as f:
            f.write(json.dumps(event.to_dict()) + "\n")

        # Notify subscribers
        for subscriber in self.subscribers.get(event.type, []):
            try:
                if asyncio.iscoroutinefunction(subscriber):
                    await subscriber(event)
                else:
                    subscriber(event)
            except Exception as e:
                logger.error(f"Subscriber error: {e}")

    def subscribe(self, event_type: EventType, handler: Callable):
        """Subscribe to events of a specific type."""
        self.subscribers[event_type].append(handler)

    def get_events(
        self, start_time: datetime | None = None, event_types: list[EventType] | None = None
    ) -> list[Event]:
        """Query events with filters."""
        result = self.events

        if start_time:
            result = [e for e in result if e.timestamp >= start_time]

        if event_types:
            result = [e for e in result if e.type in event_types]

        return result

    def create_snapshot(self, state: dict[str, Any]) -> str:
        """Create a state snapshot."""
        snapshot_id = hashlib.sha256(json.dumps(state, sort_keys=True).encode()).hexdigest()[:12]

        snapshot_file = self.snapshots_dir / f"{snapshot_id}.json"
        with open(snapshot_file, "w") as f:
            json.dump(
                {"id": snapshot_id, "timestamp": datetime.now().isoformat(), "state": state},
                f,
                indent=2,
            )

        return snapshot_id


class WorkflowState(Enum):
    """Workflow states."""

    PENDING = auto()
    RUNNING = auto()
    SUSPENDED = auto()
    COMPLETED = auto()
    FAILED = auto()
    COMPENSATING = auto()


class Workflow(ABC):
    """Abstract workflow with state machine."""

    def __init__(self, workflow_id: str, event_store: EventStore):
        self.id = workflow_id
        self.state = WorkflowState.PENDING
        self.event_store = event_store
        self.context: dict[str, Any] = {}
        self.compensation_stack: list[Callable] = []

    @abstractmethod
    async def execute(self) -> dict[str, Any]:
        """Execute the workflow."""
        pass

    async def compensate(self):
        """Run compensation logic (SAGA pattern)."""
        logger.info(f"Compensating workflow {self.id}")

        while self.compensation_stack:
            compensation = self.compensation_stack.pop()
            try:
                if asyncio.iscoroutinefunction(compensation):
                    await compensation()
                else:
                    compensation()
            except Exception as e:
                logger.error(f"Compensation error: {e}")

    async def transition(self, new_state: WorkflowState):
        """Transition to a new state."""
        old_state = self.state
        self.state = new_state

        await self.event_store.append(
            Event(
                id=f"{self.id}-transition-{time.time()}",
                type=(
                    EventType.WORKFLOW_STARTED
                    if new_state == WorkflowState.RUNNING
                    else EventType.WORKFLOW_COMPLETED
                ),
                timestamp=datetime.now(),
                payload={
                    "workflow_id": self.id,
                    "old_state": old_state.name,
                    "new_state": new_state.name,
                },
            )
        )


class SemesterPreparationWorkflow(Workflow):
    """Workflow for semester preparation tasks."""

    async def execute(self) -> dict[str, Any]:
        """Execute semester preparation workflow."""
        await self.transition(WorkflowState.RUNNING)

        try:
            # Step 1: Validate all data
            await self._validate_data()
            self.compensation_stack.append(lambda: logger.info("Reverting validation"))

            # Step 2: Generate calendars
            await self._generate_calendars()
            self.compensation_stack.append(self._cleanup_calendars)

            # Step 3: Build course materials
            await self._build_materials()
            self.compensation_stack.append(self._cleanup_materials)

            # Step 4: Setup integrations
            await self._setup_integrations()
            self.compensation_stack.append(self._cleanup_integrations)

            # Step 5: Deploy to production
            await self._deploy()

            await self.transition(WorkflowState.COMPLETED)
            return {"status": "success", "workflow_id": self.id}

        except Exception as e:
            logger.error(f"Workflow failed: {e}")
            await self.transition(WorkflowState.COMPENSATING)
            await self.compensate()
            await self.transition(WorkflowState.FAILED)
            return {"status": "failed", "error": str(e)}

    async def _validate_data(self):
        """Validate all course data."""
        await asyncio.sleep(0.1)  # Simulate work
        logger.info("Data validated")

    async def _generate_calendars(self):
        """Generate semester calendars."""
        await asyncio.sleep(0.1)
        logger.info("Calendars generated")

    async def _build_materials(self):
        """Build course materials."""
        await asyncio.sleep(0.1)
        logger.info("Materials built")

    async def _setup_integrations(self):
        """Setup LMS integrations."""
        await asyncio.sleep(0.1)
        logger.info("Integrations configured")

    async def _deploy(self):
        """Deploy to production."""
        await asyncio.sleep(0.1)
        logger.info("Deployed to production")

    async def _cleanup_calendars(self):
        """Cleanup generated calendars."""
        logger.info("Cleaning up calendars")

    async def _cleanup_materials(self):
        """Cleanup generated materials."""
        logger.info("Cleaning up materials")

    async def _cleanup_integrations(self):
        """Cleanup integrations."""
        logger.info("Cleaning up integrations")


class CircuitBreaker:
    """Circuit breaker for resilient service calls."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open

    async def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == "open":
            if (datetime.now() - self.last_failure_time).seconds > self.recovery_timeout:
                self.state = "half-open"
            else:
                raise Exception("Circuit breaker is open")

        try:
            result = (
                await func(*args, **kwargs)
                if asyncio.iscoroutinefunction(func)
                else func(*args, **kwargs)
            )

            if self.state == "half-open":
                self.state = "closed"
                self.failure_count = 0

            return result

        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = datetime.now()

            if self.failure_count >= self.failure_threshold:
                self.state = "open"
                logger.warning(f"Circuit breaker opened after {self.failure_count} failures")

            raise e


class ReactiveStream:
    """Reactive stream processor with backpressure."""

    def __init__(self, buffer_size: int = 100):
        self.buffer = deque(maxlen=buffer_size)
        self.subscribers: list[Callable] = []
        self.backpressure_threshold = buffer_size * 0.8
        self.is_backpressured = False

    async def emit(self, item: Any):
        """Emit item to stream."""
        if len(self.buffer) >= self.backpressure_threshold:
            self.is_backpressured = True
            logger.warning("Backpressure detected, slowing down")
            await asyncio.sleep(0.1)  # Apply backpressure

        self.buffer.append(item)

        # Process subscribers
        for subscriber in self.subscribers:
            try:
                if asyncio.iscoroutinefunction(subscriber):
                    await subscriber(item)
                else:
                    subscriber(item)
            except Exception as e:
                logger.error(f"Stream subscriber error: {e}")

        if len(self.buffer) < self.backpressure_threshold * 0.5:
            self.is_backpressured = False

    def subscribe(self, handler: Callable):
        """Subscribe to stream."""
        self.subscribers.append(handler)

    def map(self, transform: Callable) -> "ReactiveStream":
        """Transform stream items."""
        new_stream = ReactiveStream(self.buffer.maxlen)

        async def mapped_handler(item):
            transformed = transform(item)
            await new_stream.emit(transformed)

        self.subscribe(mapped_handler)
        return new_stream

    def filter(self, predicate: Callable) -> "ReactiveStream":
        """Filter stream items."""
        new_stream = ReactiveStream(self.buffer.maxlen)

        async def filtered_handler(item):
            if predicate(item):
                await new_stream.emit(item)

        self.subscribe(filtered_handler)
        return new_stream


class AdvancedOrchestrator:
    """Advanced orchestrator with modern patterns."""

    def __init__(self, state_dir: Path = Path("dashboard/state")):
        self.state_dir = state_dir
        self.state_dir.mkdir(exist_ok=True)

        # Core components
        self.event_store = EventStore(self.state_dir / "events")
        self.workflows: dict[str, Workflow] = {}
        self.circuit_breakers: dict[str, CircuitBreaker] = {}
        self.task_stream = ReactiveStream()
        # Track background tasks to satisfy linting and allow cleanup
        self._bg_tasks: set[asyncio.Task[Any]] = set()

        # Setup event handlers
        self._setup_event_handlers()

        # Setup reactive streams
        self._setup_streams()

    def _track_task(self, task: asyncio.Task[Any]) -> None:
        """Track a background task for lifecycle management."""
        self._bg_tasks.add(task)
        task.add_done_callback(self._bg_tasks.discard)

    def _setup_event_handlers(self):
        """Setup event-driven handlers."""
        self.event_store.subscribe(EventType.TASK_CREATED, self._handle_task_created)
        self.event_store.subscribe(EventType.TASK_COMPLETED, self._handle_task_completed)
        self.event_store.subscribe(EventType.TASK_FAILED, self._handle_task_failed)
        self.event_store.subscribe(EventType.DEADLINE_APPROACHING, self._handle_deadline)

    def _setup_streams(self):
        """Setup reactive stream processing."""
        # High priority task stream
        high_priority_stream = self.task_stream.filter(
            lambda t: t.get("priority") in ["critical", "high"]
        )
        high_priority_stream.subscribe(self._process_high_priority)

        # Optimization stream
        optimization_stream = self.task_stream.map(lambda t: self._analyze_for_optimization(t))
        optimization_stream.subscribe(self._apply_optimization)

    async def _handle_task_created(self, event: Event):
        """Handle task creation events."""
        task = event.payload
        logger.info(f"Task created: {task.get('id')}")

        # Emit to reactive stream
        await self.task_stream.emit(task)

        # Check for workflow triggers
        if task.get("category") == "semester_prep":
            workflow = SemesterPreparationWorkflow(f"workflow-{task['id']}", self.event_store)
            self.workflows[workflow.id] = workflow
            t = asyncio.create_task(workflow.execute(), name=f"workflow.execute:{workflow.id}")
            self._track_task(t)

    async def _handle_task_completed(self, event: Event):
        """Handle task completion events."""
        task_id = event.payload.get("task_id")
        logger.info(f"Task completed: {task_id}")

        # Check for dependent tasks
        await self.event_store.append(
            Event(
                id=f"dep-check-{time.time()}",
                type=EventType.DEPENDENCY_RESOLVED,
                timestamp=datetime.now(),
                payload={"resolved_task": task_id},
            )
        )

    async def _handle_task_failed(self, event: Event):
        """Handle task failure events."""
        task_id = event.payload.get("task_id")
        error = event.payload.get("error")
        logger.error(f"Task failed: {task_id} - {error}")

        # Trigger compensation if part of workflow
        for _workflow_id, workflow in self.workflows.items():
            if task_id in workflow.context.get("tasks", []):
                await workflow.compensate()

    async def _handle_deadline(self, event: Event):
        """Handle approaching deadline events."""
        deadline_info = event.payload
        logger.warning(f"Deadline approaching: {deadline_info}")

        # Trigger escalation
        await self._escalate_priority(deadline_info.get("task_id"))

    async def _process_high_priority(self, task: dict[str, Any]):
        """Process high priority tasks."""
        logger.info(f"Processing high priority task: {task.get('id')}")

        # Use circuit breaker for external calls
        if "external_api" not in self.circuit_breakers:
            self.circuit_breakers["external_api"] = CircuitBreaker()

        try:
            await self.circuit_breakers["external_api"].call(self._execute_task, task)
        except Exception as e:
            logger.error(f"Failed to execute task: {e}")

    def _analyze_for_optimization(self, task: dict[str, Any]) -> dict[str, Any]:
        """Analyze task for optimization opportunities."""
        return {
            "task": task,
            "optimizations": ["parallelize_subtasks", "cache_results", "batch_processing"],
        }

    async def _apply_optimization(self, optimization: dict[str, Any]):
        """Apply optimization suggestions."""
        task = optimization["task"]
        suggestions = optimization["optimizations"]

        if suggestions:
            await self.event_store.append(
                Event(
                    id=f"opt-{time.time()}",
                    type=EventType.OPTIMIZATION_SUGGESTED,
                    timestamp=datetime.now(),
                    payload={"task_id": task.get("id"), "suggestions": suggestions},
                )
            )

    async def _execute_task(self, task: dict[str, Any]):
        """Execute a task (placeholder for actual execution)."""
        await asyncio.sleep(0.1)  # Simulate work
        return {"status": "completed", "task_id": task.get("id")}

    async def _escalate_priority(self, task_id: str):
        """Escalate task priority."""
        logger.info(f"Escalating priority for task: {task_id}")

        await self.event_store.append(
            Event(
                id=f"escalate-{time.time()}",
                type=EventType.TASK_CREATED,
                timestamp=datetime.now(),
                payload={"task_id": task_id, "priority": "critical", "escalated": True},
            )
        )

    async def orchestrate(self, tasks: list[dict[str, Any]]) -> dict[str, Any]:
        """Main orchestration entry point."""
        results = {
            "started": datetime.now().isoformat(),
            "total_tasks": len(tasks),
            "workflows_created": 0,
            "events_processed": 0,
        }

        # Create events for all tasks
        for task in tasks:
            await self.event_store.append(
                Event(
                    id=f"task-{task['id']}-{time.time()}",
                    type=EventType.TASK_CREATED,
                    timestamp=datetime.now(),
                    payload=task,
                )
            )
            results["events_processed"] += 1

        # Process events (this would normally run continuously)
        await asyncio.sleep(1)  # Allow event processing

        results["workflows_created"] = len(self.workflows)
        results["completed"] = datetime.now().isoformat()

        # Create snapshot
        snapshot_id = self.event_store.create_snapshot(results)
        results["snapshot_id"] = snapshot_id

        return results


async def main():
    """Demonstrate advanced orchestration."""
    logging.basicConfig(level=logging.INFO)

    orchestrator = AdvancedOrchestrator()

    # Sample tasks
    tasks = [
        {
            "id": "prep-1",
            "title": "Validate course data",
            "priority": "critical",
            "category": "semester_prep",
        },
        {
            "id": "prep-2",
            "title": "Generate syllabi",
            "priority": "high",
            "category": "semester_prep",
        },
        {
            "id": "prep-3",
            "title": "Setup Blackboard",
            "priority": "medium",
            "category": "integration",
        },
    ]

    # Run orchestration
    results = await orchestrator.orchestrate(tasks)
    logger.info(f"Orchestration results: {results}")

    # Simulate deadline approaching
    await orchestrator.event_store.append(
        Event(
            id=f"deadline-{time.time()}",
            type=EventType.DEADLINE_APPROACHING,
            timestamp=datetime.now(),
            payload={
                "task_id": "prep-1",
                "deadline": (datetime.now() + timedelta(hours=2)).isoformat(),
            },
        )
    )

    # Allow event processing
    await asyncio.sleep(2)

    # Query events
    recent_events = orchestrator.event_store.get_events(
        start_time=datetime.now() - timedelta(minutes=5)
    )
    logger.info(f"Recent events: {len(recent_events)}")


if __name__ == "__main__":
    asyncio.run(main())
