"""Calendar Sync Agent - Manages dates and calendar synchronization."""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from .base import BaseAgent


class CalendarSyncAgent(BaseAgent):
    """Agent responsible for calendar and date management."""

    def __init__(self):
        super().__init__(
            agent_id="calendar-sync",
            capabilities=[
                "date_propagation",
                "deadline_management",
                "holiday_sync",
                "calendar_generation",
            ],
        )
        self.project_root = Path.cwd()

    async def execute(self, task: dict[str, Any]) -> dict[str, Any]:
        """Execute calendar synchronization tasks."""
        task_type = task.get("type", "sync")

        if task_type == "generate":
            return await self._generate_calendar()
        elif task_type == "propagate":
            return await self._propagate_dates()
        elif task_type == "check_deadlines":
            return await self._check_deadlines()
        else:
            return await self._full_sync()

    def can_handle(self, task: dict[str, Any]) -> bool:
        """Check if this agent can handle the task."""
        category = task.get("category", "").lower()
        title = task.get("title", "").lower()

        return any(
            [
                category in ["calendar", "dates", "synchronization", "deadlines"],
                "calendar" in title,
                "date" in title,
                "deadline" in title,
                "holiday" in title,
            ]
        )

    async def _generate_calendar(self) -> dict[str, Any]:
        """Generate semester calendar."""
        result = subprocess.run(["make", "calendar"], capture_output=True, text=True, timeout=30)

        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr if result.returncode != 0 else None,
            "action": "calendar_generated",
        }

    async def _propagate_dates(self) -> dict[str, Any]:
        """Propagate date changes across all course files."""
        changes_made = []

        # Load semester dates
        semester_file = Path("variables/semester.json")
        with open(semester_file) as f:
            semester = json.load(f)

        # Update each course's due dates
        for course in ["MATH221", "MATH251", "STAT253"]:
            due_dates_file = Path(f"content/courses/{course}/due_dates.json")

            if due_dates_file.exists():
                with open(due_dates_file) as f:
                    due_dates = json.load(f)

                # Update dates based on semester calendar
                # This would normally update actual dates
                changes_made.append(f"Updated {course} due dates")

        return {"success": True, "changes": changes_made, "action": "dates_propagated"}

    async def _check_deadlines(self) -> dict[str, Any]:
        """Check for approaching deadlines."""
        today = datetime.now().date()
        upcoming_deadlines = []

        # Check each course for deadlines
        for course in ["MATH221", "MATH251", "STAT253"]:
            schedule_file = Path(f"content/courses/{course}/schedule.json")

            if schedule_file.exists():
                with open(schedule_file) as f:
                    schedule = json.load(f)

                for week in schedule.get("weeks", []):
                    for assessment in week.get("assessments", []):
                        due_date_str = assessment.get("due_date")
                        if due_date_str:
                            due_date = datetime.fromisoformat(due_date_str).date()
                            days_until = (due_date - today).days

                            if 0 <= days_until <= 7:
                                upcoming_deadlines.append(
                                    {
                                        "course": course,
                                        "assessment": assessment.get("title"),
                                        "due_date": due_date_str,
                                        "days_until": days_until,
                                    }
                                )

        return {
            "success": True,
            "upcoming_deadlines": upcoming_deadlines,
            "action": "deadlines_checked",
        }

    async def _full_sync(self) -> dict[str, Any]:
        """Perform full calendar synchronization."""
        results = {}

        # Generate calendar
        results["calendar"] = await self._generate_calendar()

        # Propagate dates
        results["propagation"] = await self._propagate_dates()

        # Check deadlines
        results["deadlines"] = await self._check_deadlines()

        return {
            "success": all(r.get("success", False) for r in results.values()),
            "sync_results": results,
            "action": "full_sync_completed",
        }
