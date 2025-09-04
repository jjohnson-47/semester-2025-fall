#!/usr/bin/env python3
"""Validation gateway (scaffold).

Coalesces schema and business-rule validation prior to builds and
intelligence projections. Real implementations will compose existing
validators and new rule-based checks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from jsonschema import ValidationError, validate


@dataclass
class ValidationResult:
    ok: bool
    messages: list[str] = field(default_factory=list)

    @staticmethod
    def merge(results: list[ValidationResult]) -> ValidationResult:
        ok = all(r.ok for r in results)
        msgs = [m for r in results for m in r.messages]
        return ValidationResult(ok=ok, messages=msgs)


class ValidationGateway:
    """Aggregate validation entry point.

    Provides schema checks for v1.1.0 schedule format (backwards-compatible)
    and placeholders for business rules and intelligence preconditions.
    """

    def _load_schema(self, rel_path: str) -> dict[str, Any]:
        schema_path = Path("scripts/utils/schema/versions") / rel_path
        raw = schema_path.read_text(encoding="utf-8")
        import json

        return json.loads(raw)

    def validate_schedule_v1_1_0(self, schedule_data: dict[str, Any]) -> ValidationResult:
        try:
            schema = self._load_schema("v1_1_0/schedule.schema.json")
            validate(instance=schedule_data, schema=schema)
            return ValidationResult(ok=True)
        except ValidationError as e:
            return ValidationResult(ok=False, messages=[f"schedule v1.1.0: {e.message}"])
        except FileNotFoundError:
            return ValidationResult(ok=False, messages=["schedule schema v1.1.0 not found"])

    def validate_course_v1_1_0(self, course_data: dict[str, Any]) -> ValidationResult:
        """Validate course data against v1.1.0 course schema."""
        try:
            schema = self._load_schema("v1_1_0/course.schema.json")
            validate(instance=course_data, schema=schema)

            # Additional business rule checks
            messages = []

            # Check for _meta header (informational for now)
            if "_meta" not in course_data:
                messages.append("INFO: _meta header not present (will be required in future)")
            elif "stable_id" not in course_data.get("_meta", {}):
                messages.append("INFO: stable_id not present in _meta (recommended for tracking)")

            return ValidationResult(ok=True, messages=messages)
        except ValidationError as e:
            return ValidationResult(ok=False, messages=[f"course v1.1.0: {e.message}"])
        except FileNotFoundError:
            return ValidationResult(ok=False, messages=["course schema v1.1.0 not found"])

    def validate_for_build(self, course_id: str) -> ValidationResult:
        """Comprehensive validation for build process."""
        course_dir = Path(f"content/courses/{course_id}")
        results: list[ValidationResult] = []

        # Validate schedule if present
        schedule_file = course_dir / "schedule.json"
        if schedule_file.exists():
            import json

            data = json.loads(schedule_file.read_text(encoding="utf-8"))
            results.append(self.validate_schedule_v1_1_0(data))

        # Validate complete course if syllabus exists
        syllabus_file = course_dir / "syllabus.json"
        if syllabus_file.exists():
            import json

            course_data = json.loads(syllabus_file.read_text(encoding="utf-8"))

            # Merge schedule data if available
            if schedule_file.exists():
                schedule_data = json.loads(schedule_file.read_text(encoding="utf-8"))
                course_data["schedule"] = schedule_data

            results.append(self.validate_course_v1_1_0(course_data))

        # Default to success if no files to validate
        if not results:
            results.append(ValidationResult(ok=True))

        return ValidationResult.merge(results)

    def validate_for_intelligence(self, _course_id: str) -> ValidationResult:
        # Future: require stable IDs, parseable dates, dependency graph
        return ValidationResult(ok=True, messages=["intelligence preconditions: not enforced yet"])
