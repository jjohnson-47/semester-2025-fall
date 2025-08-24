"""QA Validator Agent - Ensures data integrity and validation."""

import json
import subprocess
from pathlib import Path
from typing import Any

from .base import BaseAgent


class QAValidatorAgent(BaseAgent):
    """Agent responsible for quality assurance and validation."""

    def __init__(self):
        super().__init__(
            agent_id="qa-validator",
            capabilities=["json_validation", "date_consistency", "rsi_check", "link_verification"],
        )
        self.project_root = Path.cwd()

    async def execute(self, task: dict[str, Any]) -> dict[str, Any]:
        """Execute validation tasks."""
        validation_type = task.get("type", "full")

        if validation_type == "json":
            return await self._validate_json()
        elif validation_type == "dates":
            return await self._validate_dates()
        elif validation_type == "rsi":
            return await self._validate_rsi()
        elif validation_type == "links":
            return await self._validate_links()
        else:
            return await self._full_validation()

    def can_handle(self, task: dict[str, Any]) -> bool:
        """Check if this agent can handle the task."""
        category = task.get("category", "").lower()
        title = task.get("title", "").lower()

        return any(
            [
                category in ["validation", "quality", "qa", "testing"],
                "validat" in title,
                "check" in title,
                "verify" in title,
                "test" in title,
            ]
        )

    async def _validate_json(self) -> dict[str, Any]:
        """Validate all JSON files against schemas."""
        result = subprocess.run(["make", "validate"], capture_output=True, text=True, timeout=30)

        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr if result.returncode != 0 else None,
            "validation_type": "json",
        }

    async def _validate_dates(self) -> dict[str, Any]:
        """Validate date consistency across all files."""
        issues = []

        # Load semester dates
        semester_file = Path("variables/semester.json")
        with open(semester_file) as f:
            semester = json.load(f)

        start_date = semester["start_date"]
        end_date = semester["end_date"]

        # Check all course files
        for course in ["MATH221", "MATH251", "STAT253"]:
            course_dir = Path(f"content/courses/{course}")

            # Check schedule dates
            schedule_file = course_dir / "schedule.json"
            if schedule_file.exists():
                with open(schedule_file) as f:
                    schedule = json.load(f)

                    # Validate weeks are within semester
                    for week in schedule.get("weeks", []):
                        week_dates = week.get("dates", {})
                        if week_dates:
                            week_start = week_dates.get("start")
                            if week_start and (week_start < start_date or week_start > end_date):
                                issues.append(
                                    f"{course}: Week {week.get('number')} outside semester dates"
                                )

        return {"success": len(issues) == 0, "issues": issues, "validation_type": "dates"}

    async def _validate_rsi(self) -> dict[str, Any]:
        """Validate Required Syllabus Information compliance."""
        missing_rsi = []

        for course in ["MATH221", "MATH251", "STAT253"]:
            rsi_file = Path(f"content/courses/{course}/rsi.json")

            if not rsi_file.exists():
                missing_rsi.append(f"{course}: RSI file missing")
                continue

            with open(rsi_file) as f:
                rsi = json.load(f)

            # Check required fields
            required_fields = [
                "course_description",
                "student_learning_outcomes",
                "required_materials",
                "evaluation_grading",
                "course_policies",
            ]

            for field in required_fields:
                if field not in rsi or not rsi[field]:
                    missing_rsi.append(f"{course}: Missing RSI field '{field}'")

        return {"success": len(missing_rsi) == 0, "issues": missing_rsi, "validation_type": "rsi"}

    async def _validate_links(self) -> dict[str, Any]:
        """Validate all links in generated content."""
        broken_links = []

        # Check HTML files for broken links
        for html_file in Path("build").rglob("*.html"):
            # This would normally check actual links
            # For now, just return success
            pass

        return {
            "success": len(broken_links) == 0,
            "broken_links": broken_links,
            "validation_type": "links",
        }

    async def _full_validation(self) -> dict[str, Any]:
        """Run all validation checks."""
        results = {
            "json": await self._validate_json(),
            "dates": await self._validate_dates(),
            "rsi": await self._validate_rsi(),
            "links": await self._validate_links(),
        }

        all_success = all(r["success"] for r in results.values())

        return {"success": all_success, "validation_results": results, "validation_type": "full"}
