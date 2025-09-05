"""Intelligent Agent Modules for Orchestration System.

Each agent is specialized for specific tasks and can be invoked
automatically by the orchestrator based on file changes or user requests.
"""

from .blackboard import BlackboardIntegratorAgent
from .calendar_sync import CalendarSyncAgent
from .course_content import CourseContentAgent
from .deployment import DeploymentManagerAgent
from .qa_validator import QAValidatorAgent

__all__ = [
    "BlackboardIntegratorAgent",
    "CalendarSyncAgent",
    "CourseContentAgent",
    "DeploymentManagerAgent",
    "QAValidatorAgent",
]

# Agent registry for automatic discovery
AGENT_REGISTRY = {
    "course-content": CourseContentAgent,
    "qa-validator": QAValidatorAgent,
    "calendar-sync": CalendarSyncAgent,
    "blackboard-integrator": BlackboardIntegratorAgent,
    "deployment-manager": DeploymentManagerAgent,
}
