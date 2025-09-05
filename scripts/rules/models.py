"""Data models for normalized course data with provenance tracking."""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class AssignmentType(Enum):
    """Types of assignments with different due date rules."""

    HOMEWORK = "homework"
    QUIZ = "quiz"
    EXAM = "exam"
    MIDTERM = "midterm"
    FINAL = "final"
    DISCUSSION = "discussion"
    PROJECT = "project"
    LAB = "lab"


class FieldSource(Enum):
    """Source of a field value for provenance."""

    ORIGINAL = "original"  # From source JSON
    COMPUTED = "computed"  # Calculated by rules
    DEFAULT = "default"  # Default value applied
    OVERRIDE = "override"  # Manual override
    INHERITED = "inherited"  # From parent/template
    RULE_APPLIED = "rule_applied"  # Modified by rule
    VALIDATED = "validated"  # Passed validation
    MIGRATED = "migrated"  # From schema migration


@dataclass
class Provenance:
    """Complete provenance chain for a value."""

    source: FieldSource
    rule: str | None = None
    timestamp: datetime | None = None
    actor: str = "system"
    confidence: float = 1.0
    original_value: Any | None = None
    transformation: str | None = None

    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = datetime.now(UTC)

    def to_dict(self) -> dict[str, Any]:
        """Serialize provenance."""
        return {
            "source": self.source.value,
            "rule": self.rule,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "actor": self.actor,
            "confidence": self.confidence,
            "original_value": self.original_value,
            "transformation": self.transformation,
        }


@dataclass
class NormalizedField:
    """A field with value and provenance tracking.

    This is the atomic unit of normalized data. Every field
    in the normalized course tracks its origin and transformations.
    """

    value: Any
    provenance: Provenance
    field_name: str | None = None
    field_type: str | None = None
    validation_rules: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def source(self) -> FieldSource:
        """Convenience accessor for provenance source."""
        return self.provenance.source

    @property
    def confidence(self) -> float:
        """Convenience accessor for confidence."""
        return self.provenance.confidence

    def with_value(self, new_value: Any, rule: str | None = None) -> "NormalizedField":
        """Create new field with updated value."""
        return NormalizedField(
            value=new_value,
            provenance=Provenance(
                source=FieldSource.RULE_APPLIED,
                rule=rule,
                original_value=self.value,
                confidence=self.confidence * 0.95,  # Slight confidence decay
            ),
            field_name=self.field_name,
            field_type=self.field_type,
            validation_rules=self.validation_rules.copy(),
            warnings=self.warnings.copy(),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize field with provenance."""
        return {
            "value": self.value,
            "provenance": self.provenance.to_dict(),
            "field_name": self.field_name,
            "field_type": self.field_type,
            "validation_rules": self.validation_rules,
            "warnings": self.warnings,
        }

    @classmethod
    def from_original(cls, value: Any, field_name: str | None = None) -> "NormalizedField":
        """Create field from original source data."""
        return cls(
            value=value, provenance=Provenance(source=FieldSource.ORIGINAL), field_name=field_name
        )

    @classmethod
    def from_default(cls, value: Any, field_name: str | None = None) -> "NormalizedField":
        """Create field from default value."""
        return cls(
            value=value,
            provenance=Provenance(source=FieldSource.DEFAULT, confidence=0.8),
            field_name=field_name,
        )


@dataclass
class CourseIdentity:
    """Core identity fields for a course."""

    code: NormalizedField
    name: NormalizedField
    title: NormalizedField | None = None
    credits: NormalizedField | None = None
    format: NormalizedField | None = None
    term: NormalizedField | None = None
    year: NormalizedField | None = None

    def get_id(self) -> str:
        """Generate stable ID for course."""
        id_string = f"{self.code.value}-{self.term.value if self.term else 'NA'}-{self.year.value if self.year else 'NA'}"
        return hashlib.sha256(id_string.encode()).hexdigest()[:16]


@dataclass
class InstructorInfo:
    """Normalized instructor information."""

    name: NormalizedField
    email: NormalizedField | None = None
    office: NormalizedField | None = None
    office_hours: NormalizedField | None = None
    phone: NormalizedField | None = None


@dataclass
class ScheduleWeek:
    """Normalized schedule week."""

    week_number: NormalizedField
    topic: NormalizedField
    readings: NormalizedField  # List[str]
    assignments: NormalizedField  # List[str]
    assessments: NormalizedField  # List[str]
    dates: NormalizedField  # Date range
    notes: NormalizedField | None = None


@dataclass
class EvaluationComponent:
    """Normalized evaluation component."""

    name: NormalizedField
    weight: NormalizedField  # Percentage
    count: NormalizedField | None = None
    drop_lowest: NormalizedField | None = None
    description: NormalizedField | None = None


@dataclass
class CoursePolicy:
    """Normalized course policy."""

    name: NormalizedField
    content: NormalizedField
    required: NormalizedField  # Boolean
    source: NormalizedField | None = None  # institutional, department, instructor


@dataclass
class NormalizedCourse:
    """Fully normalized course with all components.

    This is the complete normalized representation of a course,
    with every field tracked for provenance.
    """

    # Identity
    identity: CourseIdentity

    # Instructor
    instructor: InstructorInfo

    # Schedule
    schedule_weeks: list[ScheduleWeek] = field(default_factory=list)

    # Evaluation
    evaluation_components: list[EvaluationComponent] = field(default_factory=list)

    # Policies
    policies: list[CoursePolicy] = field(default_factory=list)

    # Important dates
    important_dates: dict[str, NormalizedField] = field(default_factory=dict)

    # Metadata
    normalized_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    schema_version: str = "1.1.0"
    normalization_rules: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def add_warning(self, warning: str) -> None:
        """Add a warning to the course."""
        self.warnings.append(warning)

    def add_error(self, error: str) -> None:
        """Add an error to the course."""
        self.errors.append(error)

    def is_valid(self) -> bool:
        """Check if course is valid (no errors)."""
        return len(self.errors) == 0

    def get_confidence(self) -> float:
        """Calculate overall confidence score."""
        all_fields = []

        # Collect all fields
        for attr_name in ["identity", "instructor"]:
            obj = getattr(self, attr_name)
            if obj:
                for field_name in obj.__dataclass_fields__:
                    field_value = getattr(obj, field_name)
                    if isinstance(field_value, NormalizedField):
                        all_fields.append(field_value)

        # Add schedule weeks
        for week in self.schedule_weeks:
            for field_name in week.__dataclass_fields__:
                field_value = getattr(week, field_name)
                if isinstance(field_value, NormalizedField):
                    all_fields.append(field_value)

        # Calculate average confidence
        if not all_fields:
            return 0.0

        total_confidence = sum(f.confidence for f in all_fields)
        return total_confidence / len(all_fields)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary with full provenance."""
        result = {
            "identity": {
                "code": self.identity.code.to_dict(),
                "name": self.identity.name.to_dict(),
                "title": self.identity.title.to_dict() if self.identity.title else None,
                "credits": self.identity.credits.to_dict() if self.identity.credits else None,
                "format": self.identity.format.to_dict() if self.identity.format else None,
                "term": self.identity.term.to_dict() if self.identity.term else None,
                "year": self.identity.year.to_dict() if self.identity.year else None,
            },
            "instructor": {
                "name": self.instructor.name.to_dict(),
                "email": self.instructor.email.to_dict() if self.instructor.email else None,
                "office": self.instructor.office.to_dict() if self.instructor.office else None,
                "office_hours": self.instructor.office_hours.to_dict()
                if self.instructor.office_hours
                else None,
            },
            "schedule_weeks": [
                {
                    "week_number": week.week_number.to_dict(),
                    "topic": week.topic.to_dict(),
                    "readings": week.readings.to_dict(),
                    "assignments": week.assignments.to_dict(),
                    "assessments": week.assessments.to_dict(),
                    "dates": week.dates.to_dict(),
                    "notes": week.notes.to_dict() if week.notes else None,
                }
                for week in self.schedule_weeks
            ],
            "evaluation_components": [
                {
                    "name": comp.name.to_dict(),
                    "weight": comp.weight.to_dict(),
                    "count": comp.count.to_dict() if comp.count else None,
                    "description": comp.description.to_dict() if comp.description else None,
                }
                for comp in self.evaluation_components
            ],
            "policies": [
                {
                    "name": policy.name.to_dict(),
                    "content": policy.content.to_dict(),
                    "required": policy.required.to_dict(),
                    "source": policy.source.to_dict() if policy.source else None,
                }
                for policy in self.policies
            ],
            "important_dates": {
                key: field.to_dict() for key, field in self.important_dates.items()
            },
            "metadata": {
                "normalized_at": self.normalized_at.isoformat(),
                "schema_version": self.schema_version,
                "normalization_rules": self.normalization_rules,
                "warnings": self.warnings,
                "errors": self.errors,
                "confidence": self.get_confidence(),
            },
        }

        return result

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)
