"""Base Agent class for all orchestration agents."""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all orchestration agents."""

    def __init__(self, agent_id: str, capabilities: list[str]):
        self.id = agent_id
        self.capabilities = capabilities
        self.status = "idle"
        self.current_task = None
        self.completed_tasks = []
        self.performance_metrics = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "average_execution_time": 0,
        }

    @abstractmethod
    async def execute(self, task: dict[str, Any]) -> dict[str, Any]:
        """Execute a task. Must be implemented by subclasses."""
        pass

    @abstractmethod
    def can_handle(self, task: dict[str, Any]) -> bool:
        """Check if this agent can handle a specific task."""
        pass

    async def pre_execute(self, task: dict[str, Any]) -> None:
        """Pre-execution hook for setup."""
        self.status = "busy"
        self.current_task = task
        logger.info(f"Agent {self.id} starting task: {task.get('id', 'unknown')}")

    async def post_execute(self, task: dict[str, Any], result: dict[str, Any]) -> None:
        """Post-execution hook for cleanup."""
        self.status = "idle"
        self.current_task = None
        self.completed_tasks.append(task.get("id", "unknown"))

        # Update metrics
        self.performance_metrics["total_executions"] += 1
        if result.get("success"):
            self.performance_metrics["successful_executions"] += 1
        else:
            self.performance_metrics["failed_executions"] += 1

        logger.info(f"Agent {self.id} completed task: {task.get('id', 'unknown')}")

    async def run_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """Main task execution wrapper."""
        start_time = datetime.now()

        try:
            # Pre-execution
            await self.pre_execute(task)

            # Execute
            result = await self.execute(task)

            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            result["execution_time"] = execution_time

            # Update average execution time
            total = self.performance_metrics["total_executions"]
            avg = self.performance_metrics["average_execution_time"]
            self.performance_metrics["average_execution_time"] = (
                (avg * (total - 1) + execution_time) / total if total > 0 else execution_time
            )

            # Post-execution
            await self.post_execute(task, result)

            return result

        except Exception as e:
            logger.error(f"Agent {self.id} failed on task {task.get('id')}: {e}")

            result = {
                "success": False,
                "error": str(e),
                "execution_time": (datetime.now() - start_time).total_seconds(),
            }

            await self.post_execute(task, result)
            return result

    def get_status(self) -> dict[str, Any]:
        """Get current agent status."""
        return {
            "id": self.id,
            "status": self.status,
            "current_task": self.current_task,
            "completed_tasks": len(self.completed_tasks),
            "capabilities": self.capabilities,
            "metrics": self.performance_metrics,
        }

    def reset_metrics(self) -> None:
        """Reset performance metrics."""
        self.performance_metrics = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "average_execution_time": 0,
        }
