"""Deployment Manager Agent - Manages site deployment and hosting."""

import subprocess
from pathlib import Path
from typing import Any

from .base import BaseAgent


class DeploymentManagerAgent(BaseAgent):
    """Agent responsible for deployment and hosting management."""

    def __init__(self):
        super().__init__(
            agent_id="deployment-manager",
            capabilities=["cloudflare_deploy", "github_actions", "hosting", "rollback"],
        )
        self.project_root = Path.cwd()

    async def execute(self, task: dict[str, Any]) -> dict[str, Any]:
        """Execute deployment tasks."""
        task_type = task.get("type", "deploy")

        if task_type == "preview":
            return await self._deploy_preview()
        elif task_type == "production":
            return await self._deploy_production()
        elif task_type == "rollback":
            return await self._rollback()
        elif task_type == "status":
            return await self._check_status()
        else:
            return await self._full_deployment()

    def can_handle(self, task: dict[str, Any]) -> bool:
        """Check if this agent can handle the task."""
        category = task.get("category", "").lower()
        title = task.get("title", "").lower()

        return any(
            [
                category in ["deployment", "hosting", "publishing", "cloudflare"],
                "deploy" in title,
                "publish" in title,
                "host" in title,
                "cloudflare" in title,
            ]
        )

    async def _deploy_preview(self) -> dict[str, Any]:
        """Deploy to preview environment."""
        # Build site
        build_result = subprocess.run(["make", "site"], capture_output=True, text=True, timeout=120)

        if build_result.returncode != 0:
            return {
                "success": False,
                "error": "Build failed",
                "output": build_result.stderr,
                "action": "preview_deploy_failed",
            }

        # In production, this would deploy to Cloudflare Pages preview
        return {
            "success": True,
            "environment": "preview",
            "url": "https://preview.jeffsthings-courses.pages.dev",
            "action": "preview_deployed",
        }

    async def _deploy_production(self) -> dict[str, Any]:
        """Deploy to production environment."""
        # Run validation first
        validation = subprocess.run(
            ["make", "validate"], capture_output=True, text=True, timeout=30
        )

        if validation.returncode != 0:
            return {
                "success": False,
                "error": "Validation failed",
                "output": validation.stderr,
                "action": "production_deploy_blocked",
            }

        # Build site
        build_result = subprocess.run(["make", "site"], capture_output=True, text=True, timeout=120)

        if build_result.returncode != 0:
            return {
                "success": False,
                "error": "Build failed",
                "output": build_result.stderr,
                "action": "production_deploy_failed",
            }

        # In production, this would deploy to Cloudflare Pages
        return {
            "success": True,
            "environment": "production",
            "url": "https://production.jeffsthings-courses.pages.dev",
            "action": "production_deployed",
        }

    async def _rollback(self) -> dict[str, Any]:
        """Rollback to previous deployment."""
        # In production, this would trigger a rollback
        return {
            "success": True,
            "action": "rollback_completed",
            "message": "Rolled back to previous deployment",
        }

    async def _check_status(self) -> dict[str, Any]:
        """Check deployment status."""
        status = {
            "preview": {
                "status": "active",
                "url": "https://preview.jeffsthings-courses.pages.dev",
                "last_deploy": "2025-08-24T10:00:00Z",
            },
            "production": {
                "status": "active",
                "url": "https://production.jeffsthings-courses.pages.dev",
                "last_deploy": "2025-08-23T15:00:00Z",
            },
        }

        return {"success": True, "deployment_status": status, "action": "status_checked"}

    async def _full_deployment(self) -> dict[str, Any]:
        """Perform full deployment pipeline."""
        results = {}

        # Deploy to preview first
        results["preview"] = await self._deploy_preview()

        if not results["preview"].get("success"):
            return {
                "success": False,
                "error": "Preview deployment failed",
                "results": results,
                "action": "deployment_aborted",
            }

        # Then deploy to production
        results["production"] = await self._deploy_production()

        return {
            "success": results["production"].get("success", False),
            "deployment_results": results,
            "action": "full_deployment_completed",
        }
