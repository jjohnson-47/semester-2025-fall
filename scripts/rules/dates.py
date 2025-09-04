#!/usr/bin/env python3
"""Central date authority (scaffold).

Encapsulates all due-date logic such as no-weekend rules and holiday
shifts, consuming the existing SemesterCalendar service. This is a
non-invasive scaffold; integration will occur via CourseRulesEngine.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from scripts.rules.models import AssignmentType, NormalizedCourse
from scripts.utils.semester_calendar import SemesterCalendar


@dataclass
class DateRules:
    """Date transformation rules with weekend avoidance and holiday handling."""

    calendar: SemesterCalendar = None
    name: str = "DateRules"
    version: str = "1.0.0"

    def __post_init__(self):
        if self.calendar is None:
            self.calendar = SemesterCalendar()

    def apply(self, context: NormalizedCourse) -> NormalizedCourse:
        """Apply date policies to assignments/assessments.

        This method is conservative: without explicit assignment
        structures in `context`, it is a no-op. Enforcement is covered
        by helper functions used by builders/services.
        """
        return context

    # ---- Enforcement helpers (used by services/builders/tests) ----
    def apply_rules(self, label: str, week_start_iso: str, holidays: list[str], *, is_assessment: bool) -> str:
        """Convenience wrapper to choose weekday, apply shifts, and format a due label.

        Returns a string like "(due Wed 09/03)".
        """
        wd = self.choose_due_weekday(label, is_assessment=is_assessment)
        wd, add = self.apply_holiday_shift(wd, holidays, label, is_assessment)
        return self.format_due(week_start_iso, wd, add)
    def apply_date_rules(self, date: datetime, assignment_type: AssignmentType = AssignmentType.HOMEWORK) -> datetime:
        """Apply date rules to shift weekends and handle holidays.
        
        Args:
            date: Original due date
            assignment_type: Type of assignment for specific rules
            
        Returns:
            Adjusted date following all rules
        """
        # Rule 1: No weekend due dates
        if self.is_weekend(date):
            return self.shift_from_weekend(date, direction="before")

        # Rule 2: Holiday handling (placeholder for future implementation)
        # TODO: Add holiday shift logic using self.calendar

        return date

    @staticmethod
    def is_weekend(date: datetime) -> bool:
        """Check if date falls on weekend (Saturday=5, Sunday=6)."""
        return date.weekday() >= 5

    @staticmethod
    def shift_from_weekend(date: datetime, direction: str = "before") -> datetime:
        """Shift date away from weekend.
        
        Args:
            date: Date to shift
            direction: "before" (to Friday) or "after" (to Monday)
            
        Returns:
            Shifted date
        """
        if direction == "before":
            # Shift to Friday
            if date.weekday() == 5:  # Saturday -> Friday
                return date - timedelta(days=1)
            elif date.weekday() == 6:  # Sunday -> Friday
                return date - timedelta(days=2)
        else:  # direction == "after"
            # Shift to Monday
            if date.weekday() == 5:  # Saturday -> Monday
                return date + timedelta(days=2)
            elif date.weekday() == 6:  # Sunday -> Monday
                return date + timedelta(days=1)

        return date

    @staticmethod
    def choose_due_weekday(label: str, is_assessment: bool = False) -> int:
        label_lower = label.lower()
        if not is_assessment:
            if "discussion" in label_lower or label_lower.startswith("bb") or "blackboard" in label_lower:
                return 2  # Wed
            return 4  # Fri default
        if "quiz" in label_lower:
            return 4  # Fri
        if "exam" in label_lower or "midterm" in label_lower or "test" in label_lower:
            return 3  # Thu
        return 4

    @staticmethod
    def apply_holiday_shift(weekday: int, holidays: list[str], label: str, is_assessment: bool) -> tuple[int, int]:
        add_days = 0
        joined = ", ".join(holidays)
        if "Fall Break" in joined and weekday in (3, 4):  # Thu/Fri
            label_lower = label.lower()
            if is_assessment and ("quiz" in label_lower or "exam" in label_lower or "test" in label_lower or "midterm" in label_lower):
                return 2, 0  # shift to Wed
            return 0, 7  # homework to next Monday
        # avoid weekends by default
        if weekday == 6:  # Sun
            return 0, add_days
        if weekday == 5:  # Sat
            return 4, add_days
        return weekday, add_days

    @staticmethod
    def format_due(week_start_iso: str, weekday: int, add_days: int = 0) -> str:
        start_dt = datetime.strptime(week_start_iso, "%Y-%m-%d")
        due_dt = start_dt + timedelta(days=weekday + add_days)
        day_label = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][weekday]
        return f"(due {day_label} {due_dt.strftime('%m/%d')})"
