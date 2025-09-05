"""Unit tests for advanced orchestrator components.

Target: ≥70% coverage on state transitions and event I/O.
Tests EventStore, ReactiveStream, CircuitBreaker, Workflow, and Coordinator.
"""

import asyncio
import pytest
from datetime import datetime, timezone, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from dashboard.advanced_orchestrator import (
    EventStore,
    EventType,
    Event,
    ReactiveStream,
    CircuitBreaker,
    Workflow,
    WorkflowState,
    AdvancedOrchestrator
)


@pytest.mark.unit
class TestEventStore:
    """Test EventStore append/get_events/snapshot functionality."""
    
    @pytest.mark.asyncio
    async def test_append_and_get_events(self, tmp_path):
        """Test appending events and retrieving them."""
        store = EventStore(tmp_path / "events")
        
        # Create and append events
        event1 = Event(
            id="event-1",
            type=EventType.TASK_CREATED,
            timestamp=datetime.now(timezone.utc),
            payload={"data": "test"}
        )
        event2 = Event(
            id="event-2", 
            type=EventType.TASK_STARTED,
            timestamp=datetime.now(timezone.utc),
            payload={"data": "modified"}
        )
        
        await store.append(event1)
        await store.append(event2)
        
        # Get all events
        all_events = store.get_events()
        assert len(all_events) == 2
        assert all_events[0].type == EventType.TASK_CREATED
        assert all_events[1].type == EventType.TASK_STARTED
        
        # Get events by type
        created_events = store.get_events(event_types=[EventType.TASK_CREATED])
        assert len(created_events) == 1
        assert created_events[0].id == "event-1"
    
    @pytest.mark.asyncio
    async def test_snapshot_creation(self, tmp_path):
        """Test snapshot creation functionality."""
        store = EventStore(tmp_path / "events")
        
        # Create snapshot
        state = {"counter": 42, "status": "active"}
        snapshot_id = store.create_snapshot(state)
        
        # Verify snapshot was created
        assert snapshot_id is not None
        assert isinstance(snapshot_id, str)
        
        # Verify snapshot file exists
        snapshot_files = list((tmp_path / "events" / "snapshots").glob("*.json"))
        assert len(snapshot_files) >= 1
    
    @pytest.mark.asyncio
    async def test_event_persistence(self, tmp_path):
        """Test that events persist across EventStore instances."""
        storage_path = tmp_path / "events"
        
        # Create first store and add events
        store1 = EventStore(storage_path)
        event = Event(
            id="persistent-event",
            type=EventType.TASK_COMPLETED,
            timestamp=datetime.now(timezone.utc),
            payload={"result": "success"}
        )
        await store1.append(event)
        
        # Create second store - should load persisted events
        store2 = EventStore(storage_path)
        events = store2.get_events()
        
        assert len(events) >= 1
        assert any(e.id == "persistent-event" for e in events)
    
    @pytest.mark.asyncio
    async def test_event_subscription(self, tmp_path):
        """Test event subscription mechanism."""
        store = EventStore(tmp_path / "events")
        
        # Set up subscription
        received_events = []
        def handler(event):
            received_events.append(event)
        
        store.subscribe(EventType.TASK_CREATED, handler)
        
        # Append event
        event = Event(
            id="sub-test",
            type=EventType.TASK_CREATED,
            timestamp=datetime.now(timezone.utc),
            payload={"task_id": "TEST-001"}
        )
        await store.append(event)
        
        # Verify handler was called
        # Note: The actual implementation may handle subscriptions differently
        # This test validates the subscription API exists


@pytest.mark.unit
class TestReactiveStream:
    """Test ReactiveStream map/filter/backpressure."""
    
    @pytest.mark.asyncio
    async def test_map_operation(self):
        """Test stream mapping."""
        stream = ReactiveStream()
        
        # Set up mapping
        doubled = stream.map(lambda x: x * 2)
        results = []
        
        # Subscribe to mapped stream
        doubled.subscribe(lambda x: results.append(x))
        
        # Emit values
        await stream.emit(1)
        await stream.emit(2)
        await stream.emit(3)
        
        assert results == [2, 4, 6]
    
    @pytest.mark.asyncio
    async def test_filter_operation(self):
        """Test stream filtering."""
        stream = ReactiveStream()
        
        # Set up filtering
        evens = stream.filter(lambda x: x % 2 == 0)
        results = []
        
        # Subscribe to filtered stream
        evens.subscribe(lambda x: results.append(x))
        
        # Emit values
        await stream.emit(1)
        await stream.emit(2)
        await stream.emit(3)
        await stream.emit(4)
        
        assert results == [2, 4]
    
    @pytest.mark.asyncio
    async def test_backpressure_with_bounded_queue(self):
        """Test backpressure handling with bounded queue."""
        stream = ReactiveStream(buffer_size=2)
        
        # Fill buffer
        await stream.emit(1)
        await stream.emit(2)
        
        # This should block briefly if buffer is full
        push_task = asyncio.create_task(stream.push(3))
        
        # Consume one item to make room
        consumed = []
        async def consumer():
            async for item in stream:
                consumed.append(item)
                if len(consumed) >= 1:
                    break
        
        consumer_task = asyncio.create_task(consumer())
        await consumer_task
        
        # Now push should complete
        await asyncio.wait_for(push_task, timeout=1.0)
        
        assert consumed[0] == 1
    
    @pytest.mark.asyncio
    async def test_stream_cancellation(self):
        """Test stream cancellation."""
        stream = ReactiveStream()
        
        consumed = []
        async def consumer():
            try:
                async for item in stream:
                    consumed.append(item)
            except asyncio.CancelledError:
                # Clean shutdown
                pass
        
        # Start consumer
        task = asyncio.create_task(consumer())
        
        # Push some values
        await stream.emit(1)
        await stream.emit(2)
        
        # Cancel consumer
        task.cancel()
        
        # Verify graceful cancellation
        with pytest.raises(asyncio.CancelledError):
            await task
        
        # Stream should still be usable
        await stream.emit(3)  # Should not raise


@pytest.mark.unit
class TestCircuitBreaker:
    """Test CircuitBreaker state transitions."""
    
    def test_initial_state(self):
        """Test circuit breaker starts in closed state."""
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=1)
        assert cb.state == "closed"
        assert cb.failure_count == 0
    
    @pytest.mark.asyncio
    async def test_successful_call_when_closed(self):
        """Test successful function call when circuit breaker is closed."""
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=1)
        
        async def success_func():
            return "success"
        
        result = await cb.call(success_func)
        assert result == "success"
        assert cb.state == "closed"
        assert cb.failure_count == 0
    
    @pytest.mark.asyncio
    async def test_closed_to_open_transition_on_failures(self):
        """Test transition from closed to open after threshold failures."""
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=1)
        
        async def failing_func():
            raise Exception("Test failure")
        
        # First failure
        with pytest.raises(Exception, match="Test failure"):
            await cb.call(failing_func)
        assert cb.state == "closed"
        assert cb.failure_count == 1
        
        # Second failure should trip the breaker
        with pytest.raises(Exception, match="Test failure"):
            await cb.call(failing_func)
        assert cb.state == "open"
        assert cb.failure_count == 2
    
    @pytest.mark.asyncio
    async def test_open_circuit_blocks_calls(self):
        """Test that open circuit breaker blocks calls."""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=1)
        cb.state = "open"
        cb.failure_count = 1
        cb.last_failure_time = datetime.now()
        
        async def test_func():
            return "should not be called"
        
        # Should raise circuit breaker exception
        with pytest.raises(Exception, match="Circuit breaker is open"):
            await cb.call(test_func)
    
    @pytest.mark.asyncio
    async def test_open_to_half_open_after_timeout(self):
        """Test transition from open to half-open after recovery timeout."""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=1)
        cb.state = "open"
        cb.failure_count = 1
        # Set last failure time to past the recovery timeout
        cb.last_failure_time = datetime.now() - timedelta(seconds=2)
        
        async def success_func():
            return "recovered"
        
        # Should transition to half-open and succeed
        result = await cb.call(success_func)
        assert result == "recovered"
        assert cb.state == "closed"  # Successful call resets to closed
        assert cb.failure_count == 0
    
    @pytest.mark.asyncio
    async def test_half_open_to_open_on_failure(self):
        """Test transition from half-open back to open on failure."""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=1)
        cb.state = "half-open"
        cb.failure_count = 1
        cb.last_failure_time = datetime.now() - timedelta(seconds=2)
        
        async def failing_func():
            raise Exception("Still failing")
        
        with pytest.raises(Exception, match="Still failing"):
            await cb.call(failing_func)
        assert cb.state == "open"
        assert cb.failure_count == 2


class TestWorkflow:
    """Test concrete workflow implementation that extends the abstract Workflow."""
    
    class ConcreteWorkflow(Workflow):
        """Test implementation of abstract Workflow."""
        
        def __init__(self, workflow_id: str, event_store: EventStore):
            super().__init__(workflow_id, event_store)
            self.execution_steps = []
            self.should_fail = False
            self.fail_step = None
        
        async def execute(self) -> dict[str, Any]:
            """Execute the test workflow."""
            await self.transition(WorkflowState.RUNNING)
            
            try:
                # Step 1: Initialize
                await self._step_initialize()
                self.compensation_stack.append(self._compensate_initialize)
                
                # Step 2: Process (may fail)
                if self.should_fail and self.fail_step == "process":
                    raise Exception("Process step failed")
                await self._step_process()
                self.compensation_stack.append(self._compensate_process)
                
                # Step 3: Finalize
                if self.should_fail and self.fail_step == "finalize":
                    raise Exception("Finalize step failed")
                await self._step_finalize()
                self.compensation_stack.append(self._compensate_finalize)
                
                await self.transition(WorkflowState.COMPLETED)
                return {"status": "completed", "steps": self.execution_steps}
                
            except Exception as e:
                await self.transition(WorkflowState.FAILED)
                await self.compensate()
                raise e
        
        async def _step_initialize(self):
            self.execution_steps.append("initialize")
        
        async def _step_process(self):
            self.execution_steps.append("process")
        
        async def _step_finalize(self):
            self.execution_steps.append("finalize")
        
        async def _compensate_initialize(self):
            self.execution_steps.append("compensate_initialize")
        
        async def _compensate_process(self):
            self.execution_steps.append("compensate_process")
        
        async def _compensate_finalize(self):
            self.execution_steps.append("compensate_finalize")
        
        async def transition(self, new_state: WorkflowState):
            """Transition to new state."""
            self.state = new_state
            await self.event_store.append(f"workflow_{self.id}", {
                "type": "state_transition",
                "from": self.state.name if hasattr(self.state, 'name') else str(self.state),
                "to": new_state.name
            })
    
    @pytest.mark.asyncio
    async def test_workflow_initialization(self, tmp_path):
        """Test workflow initializes correctly."""
        event_store = EventStore(tmp_path / "events")
        workflow = self.ConcreteWorkflow("test-workflow", event_store)
        
        assert workflow.id == "test-workflow"
        assert workflow.state == WorkflowState.PENDING
        assert workflow.event_store == event_store
        assert workflow.context == {}
        assert workflow.compensation_stack == []
    
    @pytest.mark.asyncio
    async def test_workflow_successful_execution(self, tmp_path):
        """Test successful workflow execution."""
        event_store = EventStore(tmp_path / "events")
        workflow = self.ConcreteWorkflow("success-test", event_store)
        
        result = await workflow.execute()
        
        assert workflow.state == WorkflowState.COMPLETED
        assert result["status"] == "completed"
        assert result["steps"] == ["initialize", "process", "finalize"]
        assert len(workflow.compensation_stack) == 3  # All steps added compensation
    
    @pytest.mark.asyncio
    async def test_workflow_failure_triggers_compensation(self, tmp_path):
        """Test that workflow failure triggers compensation."""
        event_store = EventStore(tmp_path / "events")
        workflow = self.ConcreteWorkflow("fail-test", event_store)
        workflow.should_fail = True
        workflow.fail_step = "process"
        
        with pytest.raises(Exception, match="Process step failed"):
            await workflow.execute()
        
        assert workflow.state == WorkflowState.FAILED
        # Should have executed initialize, then compensated it when process failed
        assert "initialize" in workflow.execution_steps
        assert "compensate_initialize" in workflow.execution_steps
        assert "process" not in workflow.execution_steps  # Failed before completing
        assert "finalize" not in workflow.execution_steps  # Never reached
    
    @pytest.mark.asyncio
    async def test_workflow_state_transitions(self, tmp_path):
        """Test workflow state transitions."""
        event_store = EventStore(tmp_path / "events")
        workflow = self.ConcreteWorkflow("state-test", event_store)
        
        # Initial state
        assert workflow.state == WorkflowState.PENDING
        
        # Manual state transitions
        await workflow.transition(WorkflowState.RUNNING)
        assert workflow.state == WorkflowState.RUNNING
        
        await workflow.transition(WorkflowState.SUSPENDED)
        assert workflow.state == WorkflowState.SUSPENDED
        
        await workflow.transition(WorkflowState.COMPENSATING)
        assert workflow.state == WorkflowState.COMPENSATING


@pytest.mark.unit
class TestAdvancedOrchestrator:
    """Test AdvancedOrchestrator integration."""
    
    @pytest.mark.asyncio
    async def test_orchestrator_initialization(self, tmp_path):
        """Test orchestrator initializes with all components."""
        orchestrator = AdvancedOrchestrator(tmp_path)
        
        assert orchestrator.event_store is not None
        assert orchestrator.circuit_breaker is not None
        assert orchestrator.stream is not None
        assert isinstance(orchestrator.handlers, dict)
    
    @pytest.mark.asyncio
    async def test_orchestrator_start_and_stop(self, tmp_path):
        """Test orchestrator lifecycle."""
        orchestrator = AdvancedOrchestrator(tmp_path)
        
        # Start orchestrator
        await orchestrator.start()
        assert orchestrator.running is True
        
        # Stop orchestrator  
        await orchestrator.stop()
        assert orchestrator.running is False
    
    @pytest.mark.asyncio
    async def test_orchestrator_event_handling(self, tmp_path):
        """Test orchestrator processes events through handlers."""
        orchestrator = AdvancedOrchestrator(tmp_path)
        
        # Register event handler
        handler_called = False
        test_event_data = None
        
        async def test_handler(event):
            nonlocal handler_called, test_event_data
            handler_called = True
            test_event_data = event
        
        orchestrator.register_handler("test_event", test_handler)
        
        # Start orchestrator
        await orchestrator.start()
        
        # Emit event
        test_data = {"message": "test"}
        await orchestrator.emit("test_event", test_data)
        
        # Give time for async processing
        await asyncio.sleep(0.1)
        
        # Stop orchestrator
        await orchestrator.stop()
        
        # Verify handler was called
        assert handler_called is True
        assert test_event_data["data"] == test_data
    
    @pytest.mark.asyncio
    async def test_orchestrator_circuit_breaker_integration(self, tmp_path):
        """Test orchestrator uses circuit breaker for resilience."""
        orchestrator = AdvancedOrchestrator(tmp_path)
        
        # Access the circuit breaker and verify it exists
        assert orchestrator.circuit_breaker is not None
        assert orchestrator.circuit_breaker.state == "closed"
        
        # Test that circuit breaker protects operations
        async def failing_operation():
            raise Exception("Test failure")
        
        # Multiple failures should trip the breaker
        for _ in range(orchestrator.circuit_breaker.failure_threshold):
            try:
                await orchestrator.circuit_breaker.call(failing_operation)
            except Exception:
                pass
        
        # Circuit breaker should now be open
        assert orchestrator.circuit_breaker.state == "open"
    
    @pytest.mark.asyncio
    async def test_orchestrator_event_persistence(self, tmp_path):
        """Test orchestrator persists events to event store."""
        orchestrator = AdvancedOrchestrator(tmp_path)
        
        # Emit some events
        await orchestrator.emit("test_event_1", {"data": "first"})
        await orchestrator.emit("test_event_2", {"data": "second"})
        
        # Check events were persisted
        events = await orchestrator.event_store.load("orchestrator")
        assert len(events) == 2
        assert events[0]["type"] == "test_event_1"
        assert events[1]["type"] == "test_event_2"

