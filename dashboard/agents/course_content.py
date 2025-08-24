"""Course Content Agent - Manages syllabi, schedules, and course materials."""

import subprocess
from pathlib import Path
from typing import Any

from .base import BaseAgent


class CourseContentAgent(BaseAgent):
    """Agent responsible for course content generation and management."""

    def __init__(self):
        super().__init__(
            agent_id="course-content",
            capabilities=["syllabi", "schedules", "materials", "validation"],
        )
        self.project_root = Path.cwd()

    async def execute(self, task: dict[str, Any]) -> dict[str, Any]:
        """Execute course content related tasks."""
        task_type = task.get("type", "")

        if "syllab" in task_type.lower():
            return await self._build_syllabi()
        elif "schedule" in task_type.lower():
            return await self._build_schedules()
        elif "weekly" in task_type.lower():
            return await self._build_weekly()
        elif "all" in task_type.lower() or "build" in task_type.lower():
            return await self._build_all()
        else:
            return await self._build_specific_course(task)

    def can_handle(self, task: dict[str, Any]) -> bool:
        """Check if this agent can handle the task."""
        category = task.get("category", "").lower()
        title = task.get("title", "").lower()

        return any(
            [
                category in ["content", "syllabi", "schedules", "materials"],
                "syllab" in title,
                "schedule" in title,
                "course" in title,
                "weekly" in title,
                "material" in title,
            ]
        )

    async def _build_syllabi(self) -> dict[str, Any]:
        """Build all course syllabi."""
        result = subprocess.run(["make", "syllabi"], capture_output=True, text=True, timeout=60)

        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr if result.returncode != 0 else None,
            "artifacts": list(Path("build/syllabi").glob("*.html")),
        }

    async def _build_schedules(self) -> dict[str, Any]:
        """Build all course schedules."""
        result = subprocess.run(["make", "schedules"], capture_output=True, text=True, timeout=60)

        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr if result.returncode != 0 else None,
            "artifacts": list(Path("build/schedules").glob("*.html")),
        }

    async def _build_weekly(self) -> dict[str, Any]:
        """Build weekly materials."""
        result = subprocess.run(["make", "weekly"], capture_output=True, text=True, timeout=60)

        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr if result.returncode != 0 else None,
            "artifacts": list(Path("build/weekly").glob("**/*.html")),
        }

    async def _build_all(self) -> dict[str, Any]:
        """Build all course materials."""
        result = subprocess.run(["make", "all"], capture_output=True, text=True, timeout=120)

        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr if result.returncode != 0 else None,
            "artifacts": {
                "syllabi": list(Path("build/syllabi").glob("*.html")),
                "schedules": list(Path("build/schedules").glob("*.html")),
                "weekly": list(Path("build/weekly").glob("**/*.html")),
            },
        }

    async def _build_specific_course(self, task: dict[str, Any]) -> dict[str, Any]:
        """Build materials for a specific course."""
        course = task.get("course", "")

        if not course:
            return {"success": False, "error": "No course specified"}

        result = subprocess.run(
            ["make", "course", f"COURSE={course}"], capture_output=True, text=True, timeout=60
        )

        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr if result.returncode != 0 else None,
            "course": course,
            "artifacts": {
                "syllabus": Path(f"build/syllabi/{course}.html"),
                "schedule": Path(f"build/schedules/{course}.html"),
            },
        }
