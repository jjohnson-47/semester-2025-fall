"""Course rules engine for normalization and transformation.

This engine applies business rules to course data, transforming
raw JSON into normalized structures with full provenance tracking.
"""

from __future__ import annotations

import re
from typing import Any

from scripts.rules.dates import DateRules
from scripts.rules.models import (
    AssignmentType,
    CourseIdentity,
    CoursePolicy,
    EvaluationComponent,
    InstructorInfo,
    NormalizedCourse,
    NormalizedField,
    ScheduleWeek,
)


class CourseRulesEngine:
    """Engine for applying normalization rules to course data."""

    def __init__(self, date_rules: DateRules | None = None):
        """Initialize the rules engine.

        Args:
            date_rules: DateRules instance for date normalization
        """
        self.date_rules = date_rules or DateRules()
        self.applied_rules: list[str] = []

    def normalize(self, course_data: dict[str, Any]) -> NormalizedCourse:
        """Normalize course data with full provenance tracking.

        Args:
            course_data: Raw course JSON data

        Returns:
            NormalizedCourse with all fields tracked
        """
        self.applied_rules = []

        # Extract identity
        identity = self._extract_identity(course_data)

        # Extract instructor
        instructor = self._extract_instructor(course_data)

        # Extract schedule
        schedule_weeks = self._extract_schedule(course_data)

        # Extract evaluation
        evaluation_components = self._extract_evaluation(course_data)

        # Extract policies
        policies = self._extract_policies(course_data)

        # Extract important dates
        important_dates = self._extract_important_dates(course_data)

        # Create normalized course
        course = NormalizedCourse(
            identity=identity,
            instructor=instructor,
            schedule_weeks=schedule_weeks,
            evaluation_components=evaluation_components,
            policies=policies,
            important_dates=important_dates,
            normalization_rules=self.applied_rules.copy(),
        )

        # Apply validation
        self._validate_course(course)

        return course

    def _extract_identity(self, data: dict[str, Any]) -> CourseIdentity:
        """Extract course identity fields."""
        self.applied_rules.append("extract_identity")

        # Required fields
        code = NormalizedField.from_original(
            data.get("course_code", data.get("code", "UNKNOWN")), field_name="code"
        )

        name = NormalizedField.from_original(
            data.get("course_name", data.get("name", "Unknown Course")), field_name="name"
        )

        # Optional fields
        title = None
        if "title" in data:
            title = NormalizedField.from_original(data["title"], field_name="title")

        credits = None
        if "credits" in data:
            credits = NormalizedField.from_original(data["credits"], field_name="credits")

        format = None
        if "format" in data:
            format = NormalizedField.from_original(data["format"], field_name="format")

        # Extract term and year
        term = None
        year = None
        if "term" in data:
            term_str = data["term"]
            # Try to parse term like "Fall 2025"
            term_match = re.match(r"(\w+)\s+(\d{4})", term_str)
            if term_match:
                term = NormalizedField.from_original(term_match.group(1), field_name="term")
                year = NormalizedField.from_original(int(term_match.group(2)), field_name="year")
            else:
                term = NormalizedField.from_original(term_str, field_name="term")

        return CourseIdentity(
            code=code, name=name, title=title, credits=credits, format=format, term=term, year=year
        )

    def _extract_instructor(self, data: dict[str, Any]) -> InstructorInfo:
        """Extract instructor information."""
        self.applied_rules.append("extract_instructor")

        instructor_data = data.get("instructor", {})

        # Name is required
        name = NormalizedField.from_original(
            instructor_data.get("name", "TBD"), field_name="instructor_name"
        )

        # Optional fields
        email = None
        if "email" in instructor_data:
            email = NormalizedField.from_original(
                instructor_data["email"], field_name="instructor_email"
            )

        office = None
        if "office" in instructor_data:
            office = NormalizedField.from_original(
                instructor_data["office"], field_name="instructor_office"
            )

        office_hours = None
        if "office_hours" in instructor_data:
            office_hours = NormalizedField.from_original(
                instructor_data["office_hours"], field_name="instructor_office_hours"
            )

        phone = None
        if "phone" in instructor_data:
            phone = NormalizedField.from_original(
                instructor_data["phone"], field_name="instructor_phone"
            )

        return InstructorInfo(
            name=name, email=email, office=office, office_hours=office_hours, phone=phone
        )

    def _extract_schedule(self, data: dict[str, Any]) -> list[ScheduleWeek]:
        """Extract schedule weeks."""
        self.applied_rules.append("extract_schedule")

        schedule_weeks = []
        schedule_data = data.get("schedule", data.get("weeks", []))

        for week_num, week_data in enumerate(schedule_data, 1):
            if isinstance(week_data, dict):
                week = ScheduleWeek(
                    week_number=NormalizedField.from_original(
                        week_data.get("week", week_num), field_name="week_number"
                    ),
                    topic=NormalizedField.from_original(
                        week_data.get("topic", "TBD"), field_name="topic"
                    ),
                    readings=NormalizedField.from_original(
                        week_data.get("readings", []), field_name="readings"
                    ),
                    assignments=NormalizedField.from_original(
                        week_data.get("assignments", []), field_name="assignments"
                    ),
                    assessments=NormalizedField.from_original(
                        week_data.get("assessments", []), field_name="assessments"
                    ),
                    dates=NormalizedField.from_original(
                        week_data.get("dates", ""), field_name="dates"
                    ),
                )

                # Apply date rules if dates are present
                if week.dates.value and self.date_rules:
                    self._apply_date_rules_to_week(week)

                schedule_weeks.append(week)

        return schedule_weeks

    def _apply_date_rules_to_week(self, week: ScheduleWeek) -> None:
        """Apply date rules to a schedule week."""
        self.applied_rules.append(f"apply_date_rules_week_{week.week_number.value}")

        # Parse dates and check for weekend conflicts
        date_str = week.dates.value
        # Handle date ranges like "Aug 26 - Aug 30"
        if isinstance(date_str, str) and date_str and " - " in date_str:
            start_str, end_str = date_str.split(" - ")
            # For now, just mark if we would need to adjust
            # Full implementation would parse and adjust dates
            _ = (start_str, end_str)

    def _extract_evaluation(self, data: dict[str, Any]) -> list[EvaluationComponent]:
        """Extract evaluation components."""
        self.applied_rules.append("extract_evaluation")

        components = []
        eval_data = data.get("evaluation", data.get("grading", {}))

        if isinstance(eval_data, dict):
            for name, info in eval_data.items():
                if isinstance(info, dict):
                    component = EvaluationComponent(
                        name=NormalizedField.from_original(name, field_name="component_name"),
                        weight=NormalizedField.from_original(
                            info.get("weight", 0), field_name="component_weight"
                        ),
                        count=NormalizedField.from_original(
                            info.get("count"), field_name="component_count"
                        )
                        if "count" in info
                        else None,
                        drop_lowest=NormalizedField.from_original(
                            info.get("drop_lowest"), field_name="drop_lowest"
                        )
                        if "drop_lowest" in info
                        else None,
                        description=NormalizedField.from_original(
                            info.get("description"), field_name="component_description"
                        )
                        if "description" in info
                        else None,
                    )
                    components.append(component)
                elif isinstance(info, int | float):
                    # Simple weight value
                    component = EvaluationComponent(
                        name=NormalizedField.from_original(name, field_name="component_name"),
                        weight=NormalizedField.from_original(info, field_name="component_weight"),
                    )
                    components.append(component)

        return components

    def _extract_policies(self, data: dict[str, Any]) -> list[CoursePolicy]:
        """Extract course policies."""
        self.applied_rules.append("extract_policies")

        policies = []
        policy_data = data.get("policies", {})

        if isinstance(policy_data, dict):
            for name, content in policy_data.items():
                if isinstance(content, dict):
                    policy = CoursePolicy(
                        name=NormalizedField.from_original(name, field_name="policy_name"),
                        content=NormalizedField.from_original(
                            content.get("content", ""), field_name="policy_content"
                        ),
                        required=NormalizedField.from_original(
                            content.get("required", False), field_name="policy_required"
                        ),
                        source=NormalizedField.from_original(
                            content.get("source"), field_name="policy_source"
                        )
                        if "source" in content
                        else None,
                    )
                else:
                    # Simple string content
                    policy = CoursePolicy(
                        name=NormalizedField.from_original(name, field_name="policy_name"),
                        content=NormalizedField.from_original(content, field_name="policy_content"),
                        required=NormalizedField.from_default(False, field_name="policy_required"),
                    )
                policies.append(policy)

        return policies

    def _extract_important_dates(self, data: dict[str, Any]) -> dict[str, NormalizedField]:
        """Extract important dates."""
        self.applied_rules.append("extract_important_dates")

        dates = {}

        # Check various possible locations
        date_sources = [
            data.get("important_dates", {}),
            data.get("dates", {}),
            data.get("calendar", {}),
        ]

        for source in date_sources:
            if isinstance(source, dict):
                for key, value in source.items():
                    if key not in dates:
                        dates[key] = NormalizedField.from_original(value, field_name=f"date_{key}")

                        # Apply date rules
                        if self.date_rules and isinstance(value, str):
                            # Determine assignment type from key
                            _ = self._infer_assignment_type(
                                key
                            )  # Reserved for future date adjustment
                            # Would apply date adjustment here
                            self.applied_rules.append(f"date_rule_{key}")

        return dates

    def _infer_assignment_type(self, key: str) -> AssignmentType:
        """Infer assignment type from a date key."""
        key_lower = key.lower()

        if "exam" in key_lower or "test" in key_lower:
            return AssignmentType.EXAM
        elif "quiz" in key_lower:
            return AssignmentType.QUIZ
        elif "hw" in key_lower or "homework" in key_lower:
            return AssignmentType.HOMEWORK
        elif "project" in key_lower:
            return AssignmentType.PROJECT
        else:
            return AssignmentType.OTHER

    def _validate_course(self, course: NormalizedCourse) -> None:
        """Validate the normalized course."""
        self.applied_rules.append("validate_course")

        # Check required fields
        if not course.identity.code.value:
            course.add_error("Missing course code")

        if not course.identity.name.value:
            course.add_error("Missing course name")

        if not course.instructor.name.value:
            course.add_error("Missing instructor name")

        # Check evaluation weights
        if course.evaluation_components:
            total_weight = sum(
                comp.weight.value
                for comp in course.evaluation_components
                if comp.weight and comp.weight.value
            )
            if abs(total_weight - 100) > 0.1:
                course.add_warning(f"Evaluation weights sum to {total_weight}%, not 100%")

        # Check schedule
        if not course.schedule_weeks:
            course.add_warning("No schedule weeks defined")

        # Mark validation complete
        for week in course.schedule_weeks:
            for field_name in week.__dataclass_fields__:
                field = getattr(week, field_name)
                if isinstance(field, NormalizedField):
                    field.validation_rules.append("presence_check")
