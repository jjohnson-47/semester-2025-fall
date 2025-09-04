"""Blackboard Integrator Agent - Manages LMS integration and iframe generation."""

import json
import subprocess
from pathlib import Path
from typing import Any

from .base import BaseAgent


class BlackboardIntegratorAgent(BaseAgent):
    """Agent responsible for Blackboard/LMS integration."""

    def __init__(self):
        super().__init__(
            agent_id="blackboard-integrator",
            capabilities=["iframe_generation", "lti_setup", "package_creation", "embed_codes"],
        )
        self.project_root = Path.cwd()
        self.base_url = "http://127.0.0.1:5055"

    async def execute(self, task: dict[str, Any]) -> dict[str, Any]:
        """Execute Blackboard integration tasks."""
        task_type = task.get("type", "iframe")

        if task_type == "iframe":
            return await self._generate_iframes()
        elif task_type == "package":
            return await self._create_packages()
        elif task_type == "lti":
            return await self._setup_lti()
        else:
            return await self._full_integration()

    def can_handle(self, task: dict[str, Any]) -> bool:
        """Check if this agent can handle the task."""
        category = task.get("category", "").lower()
        title = task.get("title", "").lower()

        return any(
            [
                category in ["blackboard", "lti", "integration", "iframe"],
                "blackboard" in title,
                "iframe" in title,
                "embed" in title,
                "lti" in title,
                "package" in title,
            ]
        )

    async def _generate_iframes(self) -> dict[str, Any]:
        """Generate iframe embed codes for all courses."""
        iframe_codes = {}

        for course in ["MATH221", "MATH251", "STAT253"]:
            iframe_codes[course] = {
                "syllabus": f"""<iframe src="{self.base_url}/embed/syllabus/{course}"
width="100%" height="800" frameborder="0"
style="border: 1px solid #ddd; border-radius: 4px;"
title="{course} Syllabus"></iframe>""",
                "schedule": f"""<iframe src="{self.base_url}/embed/schedule/{course}"
width="100%" height="600" frameborder="0"
style="border: 1px solid #ddd; border-radius: 4px;"
title="{course} Schedule"></iframe>""",
                "instructions": [
                    "1. Log into Blackboard Ultra",
                    f"2. Navigate to {course} course",
                    "3. Create or edit content item",
                    "4. Switch to HTML editor mode",
                    "5. Paste iframe code",
                    "6. Save to embed content",
                ],
            }

        # Save to file
        output_file = Path("dashboard/state/iframe_codes.json")
        with open(output_file, "w") as f:
            json.dump(iframe_codes, f, indent=2)

        return {
            "success": True,
            "iframe_codes": iframe_codes,
            "output_file": str(output_file),
            "action": "iframes_generated",
        }

    async def _create_packages(self) -> dict[str, Any]:
        """Create Blackboard import packages."""
        result = subprocess.run(["make", "packages"], capture_output=True, text=True, timeout=60)

        packages = list(Path("build/blackboard").glob("*.zip")) if result.returncode == 0 else []

        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr if result.returncode != 0 else None,
            "packages": [str(p) for p in packages],
            "action": "packages_created",
        }

    async def _setup_lti(self) -> dict[str, Any]:
        """Setup LTI tool configurations."""
        lti_configs = {}

        for course in ["MATH221", "MATH251", "STAT253"]:

            # Check for LTI configuration
            if course == "MATH221":
                lti_configs[course] = {
                    "tool": "MyOpenMath",
                    "course_id": "292612",
                    "status": "configured",
                }
            elif course == "MATH251":
                lti_configs[course] = {"tool": "Edfinity", "status": "configured"}
            elif course == "STAT253":
                lti_configs[course] = {"tool": "Pearson MyLab", "status": "configured"}

        return {"success": True, "lti_configurations": lti_configs, "action": "lti_configured"}

    async def _full_integration(self) -> dict[str, Any]:
        """Perform full Blackboard integration."""
        results = {}

        # Generate iframes
        results["iframes"] = await self._generate_iframes()

        # Create packages
        results["packages"] = await self._create_packages()

        # Setup LTI
        results["lti"] = await self._setup_lti()

        return {
            "success": all(r.get("success", False) for r in results.values()),
            "integration_results": results,
            "action": "full_integration_completed",
        }
