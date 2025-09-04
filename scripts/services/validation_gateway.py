"""Validation gateway for course data integrity.

This gateway provides centralized validation for all course operations,
ensuring data integrity, schema compliance, and business rule enforcement.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from scripts.rules.models_complete import NormalizedCourse
from scripts.services.course_service_complete import CourseService


@dataclass
class ValidationResult:
    """Result of a validation check."""

    is_valid: bool
    check_name: str
    level: str  # error, warning, info
    message: str
    field: str | None = None
    suggestion: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "is_valid": self.is_valid,
            "check_name": self.check_name,
            "level": self.level,
            "message": self.message,
            "field": self.field,
            "suggestion": self.suggestion,
        }


@dataclass
class ValidationReport:
    """Complete validation report for a course."""

    course_id: str
    timestamp: datetime
    overall_valid: bool
    confidence_score: float
    results: list[ValidationResult] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)

    @property
    def errors(self) -> list[ValidationResult]:
        """Get all error-level results."""
        return [r for r in self.results if r.level == "error"]

    @property
    def warnings(self) -> list[ValidationResult]:
        """Get all warning-level results."""
        return [r for r in self.results if r.level == "warning"]

    @property
    def info(self) -> list[ValidationResult]:
        """Get all info-level results."""
        return [r for r in self.results if r.level == "info"]

    def add_result(self, result: ValidationResult) -> None:
        """Add a validation result."""
        self.results.append(result)
        if result.level == "error" and not result.is_valid:
            self.overall_valid = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "course_id": self.course_id,
            "timestamp": self.timestamp.isoformat(),
            "overall_valid": self.overall_valid,
            "confidence_score": self.confidence_score,
            "summary": {
                "errors": len(self.errors),
                "warnings": len(self.warnings),
                "info": len(self.info),
            },
            "results": [r.to_dict() for r in self.results],
            "metrics": self.metrics,
        }


class ValidationGateway:
    """Gateway for comprehensive course validation."""

    def __init__(self, course_service: CourseService):
        """Initialize the validation gateway.

        Args:
            course_service: CourseService instance for data access
        """
        self.course_service = course_service

        # Define validation rules
        self.validators = [
            self._validate_identity,
            self._validate_instructor,
            self._validate_schedule,
            self._validate_evaluation,
            self._validate_dates,
            self._validate_policies,
            self._validate_cross_references,
        ]

    def validate_course(self, course_id: str) -> ValidationReport:
        """Perform comprehensive validation of a course.

        Args:
            course_id: Course identifier

        Returns:
            ValidationReport with all results
        """
        # Load normalized course
        try:
            course = self.course_service.load_course(course_id)
        except Exception as e:
            # Return error report if course can't be loaded
            report = ValidationReport(
                course_id=course_id,
                timestamp=datetime.now(UTC),
                overall_valid=False,
                confidence_score=0.0,
            )
            report.add_result(
                ValidationResult(
                    is_valid=False,
                    check_name="load_course",
                    level="error",
                    message=f"Failed to load course: {str(e)}",
                )
            )
            return report

        # Initialize report
        report = ValidationReport(
            course_id=course_id,
            timestamp=datetime.now(UTC),
            overall_valid=True,
            confidence_score=course.get_confidence(),
        )

        # Run all validators
        for validator in self.validators:
            validator(course, report)

        # Calculate metrics
        report.metrics = self._calculate_metrics(course, report)

        return report

    def _validate_identity(self, course: NormalizedCourse, report: ValidationReport) -> None:
        """Validate course identity fields."""
        # Check course code
        if not course.identity.code.value:
            report.add_result(
                ValidationResult(
                    is_valid=False,
                    check_name="identity_code",
                    level="error",
                    message="Course code is missing",
                    field="identity.code",
                )
            )
        elif not re.match(r"^[A-Z]{3,4}\d{3}$", course.identity.code.value):
            report.add_result(
                ValidationResult(
                    is_valid=False,
                    check_name="identity_code_format",
                    level="warning",
                    message=f"Course code '{course.identity.code.value}' doesn't match expected format",
                    field="identity.code",
                    suggestion="Use format like MATH221 or STAT253",
                )
            )

        # Check course name
        if not course.identity.name.value:
            report.add_result(
                ValidationResult(
                    is_valid=False,
                    check_name="identity_name",
                    level="error",
                    message="Course name is missing",
                    field="identity.name",
                )
            )

        # Check credits
        if course.identity.credits:
            credits = course.identity.credits.value
            if not isinstance(credits, int | float) or credits <= 0:
                report.add_result(
                    ValidationResult(
                        is_valid=False,
                        check_name="identity_credits",
                        level="warning",
                        message=f"Invalid credit value: {credits}",
                        field="identity.credits",
                        suggestion="Credits should be a positive number",
                    )
                )

    def _validate_instructor(self, course: NormalizedCourse, report: ValidationReport) -> None:
        """Validate instructor information."""
        # Check instructor name
        if not course.instructor.name.value or course.instructor.name.value == "TBD":
            report.add_result(
                ValidationResult(
                    is_valid=True,
                    check_name="instructor_name",
                    level="warning",
                    message="Instructor not yet assigned",
                    field="instructor.name",
                )
            )

        # Check email format
        if course.instructor.email and course.instructor.email.value:
            email = course.instructor.email.value
            if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email):
                report.add_result(
                    ValidationResult(
                        is_valid=False,
                        check_name="instructor_email",
                        level="warning",
                        message=f"Invalid email format: {email}",
                        field="instructor.email",
                        suggestion="Use format like instructor@college.edu",
                    )
                )

        # Check office hours
        if course.instructor.office_hours and course.instructor.office_hours.value:
            hours = course.instructor.office_hours.value
            if isinstance(hours, str) and "TBD" in hours.upper():
                report.add_result(
                    ValidationResult(
                        is_valid=True,
                        check_name="instructor_office_hours",
                        level="info",
                        message="Office hours to be determined",
                        field="instructor.office_hours",
                    )
                )

    def _validate_schedule(self, course: NormalizedCourse, report: ValidationReport) -> None:
        """Validate schedule structure and content."""
        if not course.schedule_weeks:
            report.add_result(
                ValidationResult(
                    is_valid=False,
                    check_name="schedule_weeks",
                    level="error",
                    message="No schedule weeks defined",
                    field="schedule_weeks",
                )
            )
            return

        # Check week numbers
        week_numbers = [week.week_number.value for week in course.schedule_weeks]
        expected = list(range(1, len(course.schedule_weeks) + 1))

        if week_numbers != expected:
            report.add_result(
                ValidationResult(
                    is_valid=False,
                    check_name="schedule_week_numbers",
                    level="warning",
                    message="Week numbers are not sequential",
                    field="schedule_weeks",
                    suggestion=f"Expected weeks 1-{len(course.schedule_weeks)}",
                )
            )

        # Check for empty topics
        empty_topics = [
            week.week_number.value
            for week in course.schedule_weeks
            if not week.topic.value or week.topic.value == "TBD"
        ]

        if empty_topics:
            report.add_result(
                ValidationResult(
                    is_valid=True,
                    check_name="schedule_topics",
                    level="warning",
                    message=f"Weeks {empty_topics} have undefined topics",
                    field="schedule_weeks.topic",
                )
            )

        # Typical semester length check
        num_weeks = len(course.schedule_weeks)
        if num_weeks < 14 or num_weeks > 16:
            report.add_result(
                ValidationResult(
                    is_valid=True,
                    check_name="schedule_length",
                    level="info",
                    message=f"Schedule has {num_weeks} weeks (typical is 14-16)",
                    field="schedule_weeks",
                )
            )

    def _validate_evaluation(self, course: NormalizedCourse, report: ValidationReport) -> None:
        """Validate evaluation components."""
        if not course.evaluation_components:
            report.add_result(
                ValidationResult(
                    is_valid=False,
                    check_name="evaluation_components",
                    level="error",
                    message="No evaluation components defined",
                    field="evaluation_components",
                )
            )
            return

        # Check weight total
        total_weight = sum(
            comp.weight.value
            for comp in course.evaluation_components
            if comp.weight and comp.weight.value
        )

        if abs(total_weight - 100) > 0.1:
            report.add_result(
                ValidationResult(
                    is_valid=False,
                    check_name="evaluation_weights",
                    level="error",
                    message=f"Evaluation weights sum to {total_weight}%, not 100%",
                    field="evaluation_components",
                    suggestion="Adjust component weights to total exactly 100%",
                )
            )

        # Check for negative weights
        negative_weights = [
            comp.name.value
            for comp in course.evaluation_components
            if comp.weight and comp.weight.value < 0
        ]

        if negative_weights:
            report.add_result(
                ValidationResult(
                    is_valid=False,
                    check_name="evaluation_negative_weights",
                    level="error",
                    message=f"Components have negative weights: {negative_weights}",
                    field="evaluation_components.weight",
                )
            )

    def _validate_dates(self, course: NormalizedCourse, report: ValidationReport) -> None:
        """Validate important dates and date consistency."""
        # Check for weekend due dates
        weekend_warnings = 0

        for week in course.schedule_weeks:
            # Check assignments
            if week.assignments and week.assignments.value:
                for assignment in week.assignments.value:
                    if isinstance(assignment, str) and (
                        "Saturday" in assignment or "Sunday" in assignment
                    ):
                        weekend_warnings += 1

        if weekend_warnings > 0:
            report.add_result(
                ValidationResult(
                    is_valid=True,
                    check_name="weekend_due_dates",
                    level="warning",
                    message=f"Found {weekend_warnings} potential weekend due dates",
                    suggestion="Consider moving due dates to weekdays",
                )
            )

        # Check important dates
        if course.important_dates:
            # Check for required dates
            required_dates = ["midterm", "final", "drop_deadline"]
            missing_dates = [
                date
                for date in required_dates
                if date not in [k.lower() for k in course.important_dates]
            ]

            if missing_dates:
                report.add_result(
                    ValidationResult(
                        is_valid=True,
                        check_name="important_dates",
                        level="info",
                        message=f"Missing important dates: {missing_dates}",
                        field="important_dates",
                    )
                )

    def _validate_policies(self, course: NormalizedCourse, report: ValidationReport) -> None:
        """Validate course policies."""
        if not course.policies:
            report.add_result(
                ValidationResult(
                    is_valid=True,
                    check_name="policies",
                    level="warning",
                    message="No course policies defined",
                    field="policies",
                )
            )
            return

        # Check for required policies
        required_policies = ["attendance", "late_work", "academic_integrity"]
        defined_policies = [policy.name.value.lower() for policy in course.policies]

        missing_policies = [
            policy
            for policy in required_policies
            if not any(policy in defined.lower() for defined in defined_policies)
        ]

        if missing_policies:
            report.add_result(
                ValidationResult(
                    is_valid=True,
                    check_name="required_policies",
                    level="warning",
                    message=f"Missing recommended policies: {missing_policies}",
                    field="policies",
                    suggestion="Consider adding standard academic policies",
                )
            )

    def _validate_cross_references(
        self, course: NormalizedCourse, report: ValidationReport
    ) -> None:
        """Validate cross-references between course components."""
        # Check that evaluation components match schedule references
        eval_names = {comp.name.value.lower() for comp in course.evaluation_components}

        # Collect all assessment references from schedule
        schedule_assessments: set[str] = set()
        for week in course.schedule_weeks:
            if week.assessments and week.assessments.value:
                for assessment in week.assessments.value:
                    if isinstance(assessment, str):
                        # Extract assessment type
                        assessment_lower = assessment.lower()
                        for eval_name in eval_names:
                            if eval_name in assessment_lower:
                                schedule_assessments.add(eval_name)

        # Check for evaluation components not referenced in schedule
        unreferenced = eval_names - schedule_assessments
        if unreferenced:
            report.add_result(
                ValidationResult(
                    is_valid=True,
                    check_name="cross_reference_evaluation",
                    level="info",
                    message=f"Evaluation components not found in schedule: {unreferenced}",
                    suggestion="Ensure all graded components appear in the schedule",
                )
            )

    def _calculate_metrics(
        self, course: NormalizedCourse, report: ValidationReport
    ) -> dict[str, Any]:
        """Calculate validation metrics."""
        return {
            "total_checks": len(report.results),
            "passed_checks": len([r for r in report.results if r.is_valid]),
            "failed_checks": len([r for r in report.results if not r.is_valid]),
            "coverage": {
                "identity": bool(course.identity.code.value),
                "instructor": bool(course.instructor.name.value),
                "schedule": len(course.schedule_weeks) > 0,
                "evaluation": len(course.evaluation_components) > 0,
                "policies": len(course.policies) > 0,
            },
            "completeness_score": self._calculate_completeness(course),
        }

    def _calculate_completeness(self, course: NormalizedCourse) -> float:
        """Calculate overall completeness score."""
        scores = []

        # Identity completeness
        identity_fields = [
            course.identity.code,
            course.identity.name,
            course.identity.credits,
            course.identity.term,
        ]
        identity_score = sum(1 for f in identity_fields if f and f.value) / 4
        scores.append(identity_score)

        # Instructor completeness
        instructor_fields = [
            course.instructor.name,
            course.instructor.email,
            course.instructor.office_hours,
        ]
        instructor_score = sum(1 for f in instructor_fields if f and f.value) / 3
        scores.append(instructor_score)

        # Schedule completeness
        schedule_score = min(len(course.schedule_weeks) / 14, 1.0) if course.schedule_weeks else 0.0
        scores.append(schedule_score)

        # Evaluation completeness
        if course.evaluation_components:
            eval_score = min(len(course.evaluation_components) / 5, 1.0)
        else:
            eval_score = 0.0
        scores.append(eval_score)

        return sum(scores) / len(scores) if scores else 0.0

    def validate_all_courses(self) -> dict[str, ValidationReport]:
        """Validate all available courses.

        Returns:
            Dictionary mapping course IDs to validation reports
        """
        reports = {}

        for course_id in self.course_service.get_all_courses():
            reports[course_id] = self.validate_course(course_id)

        return reports

    def generate_summary_report(self, reports: dict[str, ValidationReport]) -> dict[str, Any]:
        """Generate a summary report across all courses.

        Args:
            reports: Dictionary of validation reports by course ID

        Returns:
            Summary statistics and insights
        """
        return {
            "total_courses": len(reports),
            "valid_courses": len([r for r in reports.values() if r.overall_valid]),
            "average_confidence": sum(r.confidence_score for r in reports.values()) / len(reports)
            if reports
            else 0,
            "total_errors": sum(len(r.errors) for r in reports.values()),
            "total_warnings": sum(len(r.warnings) for r in reports.values()),
            "common_issues": self._identify_common_issues(reports),
            "timestamp": datetime.now(UTC).isoformat(),
        }

    def _identify_common_issues(self, reports: dict[str, ValidationReport]) -> list[dict[str, Any]]:
        """Identify common issues across courses."""
        issue_counts: dict[str, int] = {}

        for report in reports.values():
            for result in report.results:
                if not result.is_valid:
                    key = f"{result.check_name}:{result.level}"
                    issue_counts[key] = issue_counts.get(key, 0) + 1

        # Sort by frequency
        sorted_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)

        return [
            {"issue": issue, "count": count, "percentage": count / len(reports) * 100}
            for issue, count in sorted_issues[:5]  # Top 5 issues
        ]
