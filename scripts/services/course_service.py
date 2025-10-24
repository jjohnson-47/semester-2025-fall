"""Unified course service layer.

This service provides a centralized interface for all course operations,
managing data loading, normalization, transformation, and persistence.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.migrations.add_stable_ids_with_provenance import create_stable_course_id
from scripts.rules.dates import DateRules
from scripts.rules.engine import CourseRulesEngine
from scripts.rules.models import NormalizedCourse


@dataclass
class MetaHeader:
    """Metadata header for course documents."""

    stable_id: str
    checksum: str
    version: str = "1.1.0"
    provenance: list[dict[str, Any]] = None

    def __post_init__(self):
        if self.provenance is None:
            self.provenance = []


@dataclass
class CourseProjection:
    """A projected view of course data for a specific purpose."""

    course_id: str
    projection_type: str  # syllabus, schedule, dashboard
    data: dict[str, Any]
    metadata: dict[str, Any]
    generated_at: datetime
    checksum: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "course_id": self.course_id,
            "projection_type": self.projection_type,
            "data": self.data,
            "metadata": self.metadata,
            "generated_at": self.generated_at.isoformat(),
            "checksum": self.checksum,
        }


class CourseService:
    """Unified service for course operations."""

    def __init__(
        self,
        content_dir: Path | str,
        cache_dir: Path | None = None,
        rules_engine: CourseRulesEngine | None = None,
    ):
        """Initialize the course service.

        Args:
            content_dir: Path to content directory
            cache_dir: Path to cache directory for projections
            rules_engine: Rules engine instance
        """
        # Back-compat: allow passing a course_id as first arg (tests do this)
        default_root = Path("content")
        self._default_course_id: str | None = None
        if isinstance(content_dir, str):
            # If looks like a course id (directory exists), treat accordingly
            maybe = Path("content") / "courses" / content_dir
            if maybe.exists():
                self._default_course_id = content_dir
                self.content_dir = default_root
            else:
                self.content_dir = Path(content_dir)
        else:
            self.content_dir = Path(content_dir)
        self.cache_dir = Path(cache_dir) if cache_dir else self.content_dir / ".cache"
        self.rules_engine = rules_engine or CourseRulesEngine(DateRules())

        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Track loaded courses
        self._courses: dict[str, NormalizedCourse] = {}
        self._projections: dict[tuple[str, str], CourseProjection] = {}

    # Back-compat helper used by tests
    def get_template_context(self, view: str) -> dict[str, Any]:
        """Return a minimal template context for the given view.

        In v2 mode tests, expects 'schedule_projection' for 'schedule'.
        """
        course_id = self._default_course_id or "MATH221"
        build_mode = os.environ.get("BUILD_MODE", "legacy").lower()
        ctx: dict[str, Any] = {
            "course": {"code": course_id},
            "metadata": {"build_mode": build_mode},
        }
        if view == "schedule":
            if build_mode == "v2":
                proj = self.get_projection(course_id, "schedule")
                ctx["schedule_projection"] = proj.data
            return ctx
        if view == "syllabus":
            if build_mode == "v2":
                proj = self.get_projection(course_id, "syllabus")
                ctx["syllabus_projection"] = proj.data
            return ctx
        return ctx

    # Back-compat method used by golden tests
    def project_schedule_with_due_dates(self) -> dict[str, Any]:
        course_id = self._default_course_id or "MATH221"
        proj = self.get_projection(course_id, "schedule")
        return proj.data

    def load_course(self, course_id: str, force_reload: bool = False) -> NormalizedCourse:
        """Load and normalize a course.

        Args:
            course_id: Course identifier (e.g., "MATH221")
            force_reload: Force reload even if cached

        Returns:
            NormalizedCourse instance
        """
        if not force_reload and course_id in self._courses:
            return self._courses[course_id]

        # Load raw data
        course_data = self._load_course_data(course_id)

        # Normalize through rules engine
        normalized = self.rules_engine.normalize(course_data)

        # Cache the result
        self._courses[course_id] = normalized

        return normalized

    def _load_course_data(self, course_id: str) -> dict[str, Any]:
        """Load raw course data from files.

        Args:
            course_id: Course identifier

        Returns:
            Combined course data dictionary
        """
        course_dir = self.content_dir / "courses" / course_id

        if not course_dir.exists():
            raise ValueError(f"Course directory not found: {course_dir}")

        # Combine data from multiple sources
        combined_data = {
            "course_code": course_id,
            "_meta": {
                "version": "1.1.0",
                "stable_id": create_stable_course_id(course_id, "fall", 2025),
            },
        }

        # Load syllabus data
        syllabus_file = course_dir / "syllabus.json"
        if syllabus_file.exists():
            with open(syllabus_file) as f:
                syllabus_data = json.load(f)
                combined_data.update(syllabus_data)

        # Load schedule data
        schedule_file = course_dir / "schedule.json"
        if schedule_file.exists():
            with open(schedule_file) as f:
                schedule_data = json.load(f)
                combined_data["schedule"] = schedule_data.get("weeks", [])

        # Load evaluation data
        eval_file = course_dir / "evaluation_tools.json"
        if eval_file.exists():
            with open(eval_file) as f:
                eval_data = json.load(f)
                combined_data["evaluation"] = eval_data

        # Load RSI data
        rsi_file = course_dir / "rsi.json"
        if rsi_file.exists():
            with open(rsi_file) as f:
                rsi_data = json.load(f)
                combined_data["rsi"] = rsi_data

        # Load due dates if available
        due_dates_file = course_dir / "due_dates.json"
        if due_dates_file.exists():
            with open(due_dates_file) as f:
                due_dates = json.load(f)
                combined_data["due_dates"] = due_dates

        return combined_data

    def get_projection(
        self, course_id: str, projection_type: str, force_regenerate: bool = False
    ) -> CourseProjection:
        """Get a projected view of course data.

        Args:
            course_id: Course identifier
            projection_type: Type of projection (syllabus, schedule, dashboard)
            force_regenerate: Force regeneration even if cached

        Returns:
            CourseProjection instance
        """
        cache_key = (course_id, projection_type)

        if not force_regenerate and cache_key in self._projections:
            return self._projections[cache_key]

        # Load normalized course
        course = self.load_course(course_id)

        # Generate projection based on type
        if projection_type == "syllabus":
            projection = self._project_syllabus(course)
        elif projection_type == "schedule":
            projection = self._project_schedule(course)
        elif projection_type == "dashboard":
            projection = self._project_dashboard(course)
        else:
            raise ValueError(f"Unknown projection type: {projection_type}")

        # Cache the projection
        self._projections[cache_key] = projection

        # Optionally persist to disk
        self._save_projection(projection)

        return projection

    def _project_syllabus(self, course: NormalizedCourse) -> CourseProjection:
        """Project course data for syllabus generation."""
        data = {
            "course_code": course.identity.code.value,
            "course_name": course.identity.name.value,
            "term": course.identity.term.value if course.identity.term else "Fall 2025",
            "instructor": {
                "name": course.instructor.name.value,
                "email": course.instructor.email.value if course.instructor.email else None,
                "office": course.instructor.office.value if course.instructor.office else None,
                "office_hours": course.instructor.office_hours.value
                if course.instructor.office_hours
                else None,
            },
            "evaluation": [
                {
                    "name": comp.name.value,
                    "weight": comp.weight.value,
                    "description": comp.description.value if comp.description else None,
                }
                for comp in course.evaluation_components
            ],
            "policies": [
                {"name": policy.name.value, "content": policy.content.value}
                for policy in course.policies
            ],
            "schedule_summary": {
                "weeks": len(course.schedule_weeks),
                "topics": [week.topic.value for week in course.schedule_weeks[:5]],  # First 5 weeks
            },
        }

        checksum = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

        return CourseProjection(
            course_id=course.identity.code.value,
            projection_type="syllabus",
            data=data,
            metadata={
                "confidence": course.get_confidence(),
                "warnings": course.warnings,
                "rules_applied": course.normalization_rules,
            },
            generated_at=datetime.now(UTC),
            checksum=checksum,
        )

    def _project_schedule(self, course: NormalizedCourse) -> CourseProjection:
        """Project course data for schedule view."""
        from datetime import datetime as _dt
        from scripts.rules.dates import DateRules
        from scripts.utils.semester_calendar import SemesterCalendar

        dr = DateRules()
        cal = SemesterCalendar()
        cal_weeks = cal.get_weeks()

        # Load custom due dates if available
        custom_due_dates: dict[str, str] = {}
        course_code = course.identity.code.value
        due_dates_file = self.content_dir / "courses" / course_code / "due_dates.json"
        if due_dates_file.exists():
            with open(due_dates_file) as f:
                data = json.load(f)
                custom_due_dates = data.get("dates", {})

        def format_custom_due_date(date_str: str) -> str:
            """Format a custom due date with weekend adjustment."""
            from datetime import timedelta
            due_date = _dt.strptime(date_str, "%Y-%m-%d")

            # Apply weekend adjustment rules
            weekday = due_date.weekday()
            if weekday == 5:  # Saturday -> Friday
                due_date = due_date - timedelta(days=1)
            elif weekday == 6:  # Sunday -> Monday
                due_date = due_date + timedelta(days=1)

            day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            day_label = day_names[due_date.weekday()]
            return f"(due {day_label} {due_date.strftime('%m/%d')})"

        weeks: list[dict[str, Any]] = []
        for week in course.schedule_weeks:
            wdates = week.dates.value if week.dates else None
            start = None
            end = None
            holidays: list[str] = []
            # Prefer semester calendar mapping by week number
            try:
                wn = int(week.week_number.value)
                cal_entry = next((cw for cw in cal_weeks if cw.get("number") == wn), None)
                if cal_entry:
                    start = cal_entry.get("start")
                    end = cal_entry.get("end")
                    holidays = list(cal_entry.get("holidays") or [])
            except Exception:
                pass
            # Fallback to embedded week dates if provided
            if (start is None or end is None) and isinstance(wdates, dict):
                start = start or wdates.get("start")
                end = end or wdates.get("end")
                if not holidays and isinstance(wdates.get("holidays"), list):
                    holidays = list(wdates.get("holidays"))
            # date_range friendly string
            date_range = None
            try:
                if start and end:
                    sdt = _dt.fromisoformat(str(start)) if isinstance(start, str) else None
                    edt = _dt.fromisoformat(str(end)) if isinstance(end, str) else None
                    if sdt and edt:
                        date_range = f"{sdt.strftime('%b %d')} - {edt.strftime('%b %d')}"
            except Exception:
                pass

            # Format assignments/assessments with due labels when possible
            def fmt(
                items: list[str],
                is_assessment: bool,
                start=start,
                holidays=holidays,
            ) -> list[str]:
                out: list[str] = []
                for label in items or []:
                    try:
                        if isinstance(label, str):
                            # Check for custom due date first
                            if label in custom_due_dates:
                                due = format_custom_due_date(custom_due_dates[label])
                                out.append(f"{label} {due}")
                            elif start:
                                due = dr.apply_rules(
                                    label, str(start), holidays, is_assessment=is_assessment
                                )
                                out.append(f"{label} {due}")
                            else:
                                out.append(label)
                        else:
                            out.append(label)
                    except Exception:
                        out.append(label)
                return out

            weeks.append(
                {
                    "week": week.week_number.value,
                    "topic": week.topic.value,
                    "dates": wdates,
                    "date_range": date_range,
                    "readings": week.readings.value,
                    "assignments": fmt(week.assignments.value, is_assessment=False),
                    "assessments": fmt(week.assessments.value, is_assessment=True),
                    "notes": week.notes.value if week.notes else None,
                }
            )

        data = {
            "course_code": course.identity.code.value,
            "weeks": weeks,
            "important_dates": {key: field.value for key, field in course.important_dates.items()},
        }

        checksum = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

        return CourseProjection(
            course_id=course.identity.code.value,
            projection_type="schedule",
            data=data,
            metadata={
                "total_weeks": len(course.schedule_weeks),
                "has_dates": any(week.dates.value for week in course.schedule_weeks),
            },
            generated_at=datetime.now(UTC),
            checksum=checksum,
        )

    def _project_dashboard(self, course: NormalizedCourse) -> CourseProjection:
        """Project course data for dashboard view."""
        # Calculate metrics
        total_assignments = sum(
            len(week.assignments.value) if week.assignments.value else 0
            for week in course.schedule_weeks
        )

        total_assessments = sum(
            len(week.assessments.value) if week.assessments.value else 0
            for week in course.schedule_weeks
        )

        data = {
            "course_code": course.identity.code.value,
            "course_name": course.identity.name.value,
            "instructor": course.instructor.name.value,
            "metrics": {
                "total_weeks": len(course.schedule_weeks),
                "total_assignments": total_assignments,
                "total_assessments": total_assessments,
                "evaluation_components": len(course.evaluation_components),
                "confidence_score": course.get_confidence(),
            },
            "status": {
                "is_valid": course.is_valid(),
                "warnings": len(course.warnings),
                "errors": len(course.errors),
            },
            "last_updated": datetime.now(UTC).isoformat(),
        }

        checksum = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

        return CourseProjection(
            course_id=course.identity.code.value,
            projection_type="dashboard",
            data=data,
            metadata={"warnings": course.warnings, "errors": course.errors},
            generated_at=datetime.now(UTC),
            checksum=checksum,
        )

    def _save_projection(self, projection: CourseProjection) -> None:
        """Save a projection to disk cache."""
        projection_dir = self.cache_dir / "projections" / projection.course_id
        projection_dir.mkdir(parents=True, exist_ok=True)

        projection_file = projection_dir / f"{projection.projection_type}.json"

        with open(projection_file, "w") as f:
            json.dump(projection.to_dict(), f, indent=2, default=str)

    def validate_course(self, course_id: str) -> dict[str, Any]:
        """Validate a course and return validation results.

        Args:
            course_id: Course identifier

        Returns:
            Validation results dictionary
        """
        course = self.load_course(course_id)

        return {
            "course_id": course_id,
            "is_valid": course.is_valid(),
            "confidence": course.get_confidence(),
            "warnings": course.warnings,
            "errors": course.errors,
            "rules_applied": course.normalization_rules,
        }

    def get_all_courses(self) -> list[str]:
        """Get list of all available courses.

        Returns:
            List of course identifiers
        """
        courses_dir = self.content_dir / "courses"

        if not courses_dir.exists():
            return []

        return [d.name for d in courses_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
