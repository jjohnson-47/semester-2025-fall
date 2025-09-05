"""Unit tests for orchestration agent components.

Tests the master orchestration agent and coordinator interactions.
"""

import asyncio
import json
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from dashboard.orchestration_agent import (
    MasterOrchestrationAgent
)
from dashboard.orchestrator import (
    AgentCoordinator,
    TaskOrchestrator
)


@pytest.mark.unit
class TestOrchestrationAgent:
    """Test the main OrchestrationAgent."""
    
    @pytest.fixture
    def agent(self, tmp_path):
        """Create an orchestration agent with temp directory."""
        return OrchestrationAgent(
            name="test-agent",
            capabilities=["task_management", "validation"],
            state_dir=tmp_path
        )
    
    def test_agent_initialization(self, agent):
        """Test agent initializes with correct attributes."""
        assert agent.name == "test-agent"
        assert "task_management" in agent.capabilities
        assert "validation" in agent.capabilities
        assert agent.state == OrchestrationState.IDLE
    
    @pytest.mark.asyncio
    async def test_agent_state_transitions(self, agent):
        """Test agent state transitions."""
        # Start idle
        assert agent.state == OrchestrationState.IDLE
        
        # Transition to planning
        agent.transition_to(OrchestrationState.PLANNING)
        assert agent.state == OrchestrationState.PLANNING
        
        # Transition to executing
        agent.transition_to(OrchestrationState.EXECUTING)
        assert agent.state == OrchestrationState.EXECUTING
        
        # Transition to monitoring
        agent.transition_to(OrchestrationState.MONITORING)
        assert agent.state == OrchestrationState.MONITORING
        
        # Back to idle
        agent.transition_to(OrchestrationState.IDLE)
        assert agent.state == OrchestrationState.IDLE
    
    @pytest.mark.asyncio
    async def test_agent_message_handling(self, agent):
        """Test agent processes messages."""
        handled_messages = []
        
        async def mock_handler(msg):
            handled_messages.append(msg)
        
        agent.register_handler("test_message", mock_handler)
        
        # Send message
        message = AgentMessage(
            type="test_message",
            payload={"data": "test"},
            sender="coordinator"
        )
        
        await agent.handle_message(message)
        
        assert len(handled_messages) == 1
        assert handled_messages[0].payload["data"] == "test"
    
    @pytest.mark.asyncio
    async def test_agent_capability_check(self, agent):
        """Test agent capability checking."""
        assert agent.has_capability("task_management")
        assert agent.has_capability("validation")
        assert not agent.has_capability("deployment")
    
    @pytest.mark.asyncio
    async def test_agent_persistence(self, tmp_path):
        """Test agent state persistence."""
        state_file = tmp_path / "agent_state.json"
        
        # Create agent with state
        agent = OrchestrationAgent(
            name="persistent-agent",
            capabilities=["testing"],
            state_dir=tmp_path
        )
        
        agent.state = OrchestrationState.EXECUTING
        agent.metadata = {"task_count": 5, "last_run": "2025-09-01"}
        
        # Save state
        await agent.save_state()
        assert state_file.exists()
        
        # Load state in new agent
        new_agent = OrchestrationAgent(
            name="persistent-agent",
            capabilities=["testing"],
            state_dir=tmp_path
        )
        await new_agent.load_state()
        
        assert new_agent.state == OrchestrationState.EXECUTING
        assert new_agent.metadata["task_count"] == 5
        assert new_agent.metadata["last_run"] == "2025-09-01"


@pytest.mark.unit
class TestAgentCoordinator:
    """Test AgentCoordinator multi-agent management."""
    
    @pytest.fixture
    def coordinator(self):
        """Create a coordinator instance."""
        return AgentCoordinator()
    
    def test_coordinator_initialization(self, coordinator):
        """Test coordinator starts with no agents."""
        assert len(coordinator.agents) == 0
        assert coordinator.is_running is False
    
    @pytest.mark.asyncio
    async def test_coordinator_agent_registration(self, coordinator):
        """Test registering agents with coordinator."""
        # Create mock agents
        agent1 = Mock(spec=OrchestrationAgent)
        agent1.name = "agent-1"
        agent1.capabilities = ["task_management"]
        
        agent2 = Mock(spec=OrchestrationAgent)
        agent2.name = "agent-2"
        agent2.capabilities = ["validation"]
        
        # Register agents
        coordinator.register_agent(agent1)
        coordinator.register_agent(agent2)
        
        assert len(coordinator.agents) == 2
        assert "agent-1" in coordinator.agents
        assert "agent-2" in coordinator.agents
    
    @pytest.mark.asyncio
    async def test_coordinator_capability_routing(self, coordinator):
        """Test coordinator routes tasks based on capabilities."""
        # Create agents with different capabilities
        task_agent = Mock(spec=OrchestrationAgent)
        task_agent.name = "task-agent"
        task_agent.capabilities = ["task_management"]
        task_agent.has_capability = lambda c: c == "task_management"
        
        validation_agent = Mock(spec=OrchestrationAgent)
        validation_agent.name = "validation-agent"
        validation_agent.capabilities = ["validation"]
        validation_agent.has_capability = lambda c: c == "validation"
        
        coordinator.register_agent(task_agent)
        coordinator.register_agent(validation_agent)
        
        # Find agents by capability
        task_agents = coordinator.find_agents_by_capability("task_management")
        assert len(task_agents) == 1
        assert task_agents[0].name == "task-agent"
        
        validation_agents = coordinator.find_agents_by_capability("validation")
        assert len(validation_agents) == 1
        assert validation_agents[0].name == "validation-agent"
    
    @pytest.mark.asyncio
    async def test_coordinator_broadcast_message(self, coordinator):
        """Test coordinator broadcasts messages to all agents."""
        received_messages = []
        
        # Create mock agents
        for i in range(3):
            agent = Mock(spec=OrchestrationAgent)
            agent.name = f"agent-{i}"
            agent.handle_message = AsyncMock(
                side_effect=lambda msg: received_messages.append(msg)
            )
            coordinator.register_agent(agent)
        
        # Broadcast message
        message = AgentMessage(
            type="broadcast",
            payload={"announcement": "test"},
            sender="coordinator"
        )
        
        await coordinator.broadcast(message)
        
        # All agents should receive the message
        assert len(received_messages) == 3
        for msg in received_messages:
            assert msg.type == "broadcast"
            assert msg.payload["announcement"] == "test"
    
    @pytest.mark.asyncio
    async def test_coordinator_directed_message(self, coordinator):
        """Test coordinator sends directed messages."""
        target_received = []
        other_received = []
        
        # Create target agent
        target_agent = Mock(spec=OrchestrationAgent)
        target_agent.name = "target"
        target_agent.handle_message = AsyncMock(
            side_effect=lambda msg: target_received.append(msg)
        )
        
        # Create other agent
        other_agent = Mock(spec=OrchestrationAgent)
        other_agent.name = "other"
        other_agent.handle_message = AsyncMock(
            side_effect=lambda msg: other_received.append(msg)
        )
        
        coordinator.register_agent(target_agent)
        coordinator.register_agent(other_agent)
        
        # Send directed message
        message = AgentMessage(
            type="direct",
            payload={"data": "secret"},
            sender="coordinator",
            recipient="target"
        )
        
        await coordinator.send_to(message, "target")
        
        # Only target should receive
        assert len(target_received) == 1
        assert len(other_received) == 0
        assert target_received[0].payload["data"] == "secret"


@pytest.mark.unit
class TestTaskOrchestrator:
    """Test TaskOrchestrator workflow coordination."""
    
    @pytest.fixture
    def orchestrator(self, tmp_path):
        """Create a task orchestrator."""
        return TaskOrchestrator(state_dir=tmp_path)
    
    @pytest.mark.asyncio
    async def test_orchestrator_task_planning(self, orchestrator):
        """Test orchestrator plans task execution."""
        # Create mock task
        task = {
            "id": "TEST-001",
            "title": "Test Task",
            "dependencies": [],
            "effort_hours": 2
        }
        
        # Plan execution
        plan = await orchestrator.plan_task_execution(task)
        
        assert plan is not None
        assert plan["task_id"] == "TEST-001"
        assert "steps" in plan
        assert "estimated_duration" in plan
    
    @pytest.mark.asyncio
    async def test_orchestrator_dependency_resolution(self, orchestrator):
        """Test orchestrator resolves task dependencies."""
        # Create tasks with dependencies
        tasks = [
            {"id": "A", "dependencies": []},
            {"id": "B", "dependencies": ["A"]},
            {"id": "C", "dependencies": ["A", "B"]},
            {"id": "D", "dependencies": ["C"]}
        ]
        
        # Resolve execution order
        order = await orchestrator.resolve_execution_order(tasks)
        
        # Should be topologically sorted
        assert order == ["A", "B", "C", "D"]
        
        # Verify each task comes after its dependencies
        for i, task_id in enumerate(order):
            task = next(t for t in tasks if t["id"] == task_id)
            for dep in task["dependencies"]:
                dep_index = order.index(dep)
                assert dep_index < i
    
    @pytest.mark.asyncio
    async def test_orchestrator_parallel_task_identification(self, orchestrator):
        """Test orchestrator identifies tasks that can run in parallel."""
        # Create tasks - B and C can run in parallel after A
        tasks = [
            {"id": "A", "dependencies": []},
            {"id": "B", "dependencies": ["A"]},
            {"id": "C", "dependencies": ["A"]},
            {"id": "D", "dependencies": ["B", "C"]}
        ]
        
        # Get parallel groups
        parallel_groups = await orchestrator.identify_parallel_groups(tasks)
        
        assert len(parallel_groups) == 3
        assert parallel_groups[0] == ["A"]  # First group
        assert set(parallel_groups[1]) == {"B", "C"}  # Can run in parallel
        assert parallel_groups[2] == ["D"]  # After B and C
    
    @pytest.mark.asyncio
    async def test_orchestrator_resource_allocation(self, orchestrator):
        """Test orchestrator allocates resources to agents."""
        # Mock available agents
        agents = [
            Mock(name="agent-1", capacity=2),
            Mock(name="agent-2", capacity=3),
            Mock(name="agent-3", capacity=1)
        ]
        
        # Tasks to allocate
        tasks = [
            {"id": "T1", "effort": 1},
            {"id": "T2", "effort": 2},
            {"id": "T3", "effort": 1},
            {"id": "T4", "effort": 1}
        ]
        
        # Allocate tasks to agents
        allocation = await orchestrator.allocate_tasks_to_agents(tasks, agents)
        
        # Verify allocation respects capacity
        for agent_name, assigned_tasks in allocation.items():
            agent = next(a for a in agents if a.name == agent_name)
            total_effort = sum(t["effort"] for t in assigned_tasks)
            assert total_effort <= agent.capacity
    
    @pytest.mark.asyncio
    async def test_orchestrator_progress_tracking(self, orchestrator):
        """Test orchestrator tracks task progress."""
        # Start tracking
        await orchestrator.start_tracking("TEST-001")
        
        # Update progress
        await orchestrator.update_progress("TEST-001", 25)
        await orchestrator.update_progress("TEST-001", 50)
        await orchestrator.update_progress("TEST-001", 100)
        
        # Get progress history
        history = await orchestrator.get_progress_history("TEST-001")
        
        assert len(history) == 3
        assert history[0]["progress"] == 25
        assert history[1]["progress"] == 50
        assert history[2]["progress"] == 100
    
    @pytest.mark.asyncio
    async def test_orchestrator_failure_handling(self, orchestrator):
        """Test orchestrator handles task failures."""
        # Simulate task failure
        await orchestrator.report_failure("TEST-001", "Network error")
        
        # Check failure is recorded
        failures = await orchestrator.get_failures()
        assert len(failures) == 1
        assert failures[0]["task_id"] == "TEST-001"
        assert failures[0]["reason"] == "Network error"
        
        # Test retry logic
        retry_plan = await orchestrator.plan_retry("TEST-001")
        assert retry_plan is not None
        assert retry_plan["attempt"] == 2
        assert "backoff_seconds" in retry_plan


@pytest.mark.unit
class TestOrchestrationIntegration:
    """Test integration between orchestration components."""
    
    @pytest.mark.asyncio
    async def test_full_orchestration_flow(self, tmp_path):
        """Test complete orchestration workflow."""
        # Create coordinator
        coordinator = AgentCoordinator()
        
        # Create specialized agents
        planner = OrchestrationAgent(
            name="planner",
            capabilities=["planning"],
            state_dir=tmp_path
        )
        
        executor = OrchestrationAgent(
            name="executor",
            capabilities=["execution"],
            state_dir=tmp_path
        )
        
        monitor = OrchestrationAgent(
            name="monitor",
            capabilities=["monitoring"],
            state_dir=tmp_path
        )
        
        # Register agents
        coordinator.register_agent(planner)
        coordinator.register_agent(executor)
        coordinator.register_agent(monitor)
        
        # Create orchestrator
        orchestrator = TaskOrchestrator(state_dir=tmp_path)
        
        # Simulate task workflow
        task = {
            "id": "INTEGRATION-001",
            "title": "Integration Test Task",
            "dependencies": [],
            "effort_hours": 1
        }
        
        # Plan phase
        plan = await orchestrator.plan_task_execution(task)
        assert plan is not None
        
        # Send plan to planner agent
        plan_message = AgentMessage(
            type="plan_task",
            payload=plan,
            sender="orchestrator",
            recipient="planner"
        )
        await coordinator.send_to(plan_message, "planner")
        
        # Execute phase
        execute_message = AgentMessage(
            type="execute_task",
            payload={"task_id": task["id"]},
            sender="planner",
            recipient="executor"
        )
        await coordinator.send_to(execute_message, "executor")
        
        # Monitor phase
        monitor_message = AgentMessage(
            type="monitor_task",
            payload={"task_id": task["id"]},
            sender="executor",
            recipient="monitor"
        )
        await coordinator.send_to(monitor_message, "monitor")
        
        # Verify all agents transitioned states appropriately
        assert planner.state != OrchestrationState.IDLE
        assert executor.state != OrchestrationState.IDLE
        assert monitor.state != OrchestrationState.IDLE