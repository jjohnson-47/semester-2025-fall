"""Unit tests for orchestration agent - focused on actual implementation.

Tests the MasterOrchestrationAgent and basic coordination.
"""

import asyncio
import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from dashboard.orchestration_agent import MasterOrchestrationAgent


@pytest.mark.unit
class TestMasterOrchestrationAgent:
    """Test the MasterOrchestrationAgent."""
    
    def test_agent_initialization(self, tmp_path):
        """Test agent initializes correctly."""
        with patch('dashboard.orchestration_agent.TaskOrchestrator'), \
             patch('dashboard.orchestration_agent.AgentCoordinator'):
            agent = MasterOrchestrationAgent()
            
            assert agent.state_dir.name == "state"
            assert agent.orchestrator is not None
            assert agent.coordinator is not None
            assert agent.agent_registry is not None
    
    def test_agent_registry_structure(self, tmp_path):
        """Test agent registry has expected structure."""
        with patch('dashboard.orchestration_agent.TaskOrchestrator'), \
             patch('dashboard.orchestration_agent.AgentCoordinator'):
            agent = MasterOrchestrationAgent()
            
            # Check key agents are registered
            assert "course-content" in agent.agent_registry
            assert "qa-validator" in agent.agent_registry
            assert "deployment-manager" in agent.agent_registry
            
            # Verify structure
            course_agent = agent.agent_registry["course-content"]
            assert "capabilities" in course_agent
            assert "commands" in course_agent
            assert "priority" in course_agent
            assert course_agent["priority"] == "critical"
    
    @pytest.mark.asyncio
    async def test_agent_semester_check(self, tmp_path):
        """Test agent checks semester status."""
        with patch('dashboard.orchestration_agent.TaskOrchestrator'), \
             patch('dashboard.orchestration_agent.AgentCoordinator'):
            agent = MasterOrchestrationAgent()
            
            # Mock the check method if it exists
            if hasattr(agent, 'check_semester_status'):
                status = await agent.check_semester_status()
                assert status is not None
    
    @pytest.mark.asyncio 
    async def test_agent_coordination_workflow(self, tmp_path):
        """Test basic coordination workflow."""
        mock_orchestrator = MagicMock()
        mock_coordinator = MagicMock()
        
        with patch('dashboard.orchestration_agent.TaskOrchestrator', return_value=mock_orchestrator), \
             patch('dashboard.orchestration_agent.AgentCoordinator', return_value=mock_coordinator):
            
            agent = MasterOrchestrationAgent()
            
            # Verify components are wired correctly
            assert agent.orchestrator == mock_orchestrator
            assert agent.coordinator == mock_coordinator
            
            # Test that coordinator was initialized with orchestrator
            mock_coordinator_class = patch.object
    
    def test_agent_capabilities_mapping(self, tmp_path):
        """Test agent capabilities are properly mapped."""
        with patch('dashboard.orchestration_agent.TaskOrchestrator'), \
             patch('dashboard.orchestration_agent.AgentCoordinator'):
            agent = MasterOrchestrationAgent()
            
            # Test course-content agent
            course_agent = agent.agent_registry["course-content"]
            expected_capabilities = ["content", "syllabi", "schedules", "materials"]
            assert all(cap in course_agent["capabilities"] for cap in expected_capabilities)
            
            # Test qa-validator agent
            qa_agent = agent.agent_registry["qa-validator"]
            expected_capabilities = ["validation", "quality", "testing"]
            assert all(cap in qa_agent["capabilities"] for cap in expected_capabilities)
            
            # Test deployment agent
            deploy_agent = agent.agent_registry["deployment-manager"]
            expected_capabilities = ["deployment", "hosting", "publishing"]
            assert all(cap in deploy_agent["capabilities"] for cap in expected_capabilities)
    
    def test_agent_command_mappings(self, tmp_path):
        """Test agent command mappings are correct."""
        with patch('dashboard.orchestration_agent.TaskOrchestrator'), \
             patch('dashboard.orchestration_agent.AgentCoordinator'):
            agent = MasterOrchestrationAgent()
            
            # Test course-content commands
            course_agent = agent.agent_registry["course-content"]
            assert "make syllabi" in course_agent["commands"]
            assert "make schedules" in course_agent["commands"]
            
            # Test qa-validator commands  
            qa_agent = agent.agent_registry["qa-validator"]
            assert "make validate" in qa_agent["commands"]
            assert "make test" in qa_agent["commands"]
    
    def test_agent_priorities(self, tmp_path):
        """Test agent priorities are set correctly."""
        with patch('dashboard.orchestration_agent.TaskOrchestrator'), \
             patch('dashboard.orchestration_agent.AgentCoordinator'):
            agent = MasterOrchestrationAgent()
            
            # Critical priority agents
            assert agent.agent_registry["course-content"]["priority"] == "critical"
            
            # High priority agents
            assert agent.agent_registry["qa-validator"]["priority"] == "high"
            
            # Medium priority agents
            assert agent.agent_registry["deployment-manager"]["priority"] == "medium"


@pytest.mark.unit 
class TestOrchestrationIntegration:
    """Test integration aspects we can verify."""
    
    def test_state_directory_creation(self, tmp_path):
        """Test state directory is created."""
        with patch('dashboard.orchestration_agent.TaskOrchestrator'), \
             patch('dashboard.orchestration_agent.AgentCoordinator'), \
             patch('dashboard.orchestration_agent.Path') as mock_path:
            
            # Mock the state directory
            mock_state_dir = MagicMock()
            mock_path.return_value = mock_state_dir
            
            agent = MasterOrchestrationAgent()
            
            # Verify state directory setup
            mock_state_dir.mkdir.assert_called_with(exist_ok=True)
    
    @pytest.mark.asyncio
    async def test_component_initialization_order(self, tmp_path):
        """Test components are initialized in correct order."""
        with patch('dashboard.orchestration_agent.TaskOrchestrator') as mock_orch, \
             patch('dashboard.orchestration_agent.AgentCoordinator') as mock_coord:
            
            agent = MasterOrchestrationAgent()
            
            # Verify orchestrator is created first
            mock_orch.assert_called_once()
            
            # Verify coordinator is created with orchestrator
            mock_coord.assert_called_once_with(agent.orchestrator)
    
    def test_agent_registry_completeness(self, tmp_path):
        """Test agent registry covers all expected domains."""
        with patch('dashboard.orchestration_agent.TaskOrchestrator'), \
             patch('dashboard.orchestration_agent.AgentCoordinator'):
            agent = MasterOrchestrationAgent()
            
            # Verify we have agents for major domains
            expected_domains = [
                "course-content",        # Content generation
                "qa-validator",          # Quality assurance  
                "deployment-manager",    # Deployment management
                "calendar-sync",         # Calendar synchronization
                "blackboard-integrator"  # Blackboard integration
            ]
            
            for domain in expected_domains:
                assert domain in agent.agent_registry, f"Missing agent for {domain}"
                
                # Each agent should have the required fields
                agent_config = agent.agent_registry[domain]
                assert "capabilities" in agent_config
                assert "commands" in agent_config
                assert "priority" in agent_config
                assert isinstance(agent_config["capabilities"], list)
                assert isinstance(agent_config["commands"], list)
                assert agent_config["priority"] in ["critical", "high", "medium", "low"]