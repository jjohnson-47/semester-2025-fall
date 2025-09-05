#!/usr/bin/env python3
"""Central date authority with weekend/holiday enforcement.

Encapsulates due-date logic such as no-weekend rules and holiday shifts,
consuming the existing SemesterCalendar service. This module also adds:
- Assignment-type preferences (e.g., homework→Friday, exams→Thursday)
- Holiday awareness using SemesterCalendar.get_holidays
- Shift provenance logging for audit/reporting

Backward-compatible helpers (choose_due_weekday, apply_holiday_shift, format_due)
are retained for existing call sites and tests.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from scripts.rules.models import AssignmentType, NormalizedCourse
from scripts.utils.semester_calendar import SemesterCalendar


@dataclass
class DateRules:
    """Date transformation rules with weekend avoidance and holiday handling.

    Adds assignment-type preferences, holiday detection, and shift provenance
    logging while preserving the prior helper API.
    """

    calendar: SemesterCalendar | None = None
    name: str = "DateRules"
    version: str = "1.1.0"
    shift_log: list[DateShift] = field(default_factory=list)

    def __post_init__(self) -> None:
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
    class ShiftDirection(Enum):
        EARLIER = "earlier"
        LATER = "later"
        NEAREST = "nearest"

    @dataclass
    class DateShift:
        original: datetime
        shifted: datetime
        reason: str
        rule: str

    def _type_preferences(self) -> dict[AssignmentType, dict[str, Any]]:
        """Default weekday preferences and shift directions by type.

        Weekday index: Monday=0 .. Sunday=6
        """
        return {
            AssignmentType.HOMEWORK: {
                "preferred_day": 4,
                "shift": self.ShiftDirection.EARLIER,
            },  # Fri
            AssignmentType.QUIZ: {"preferred_day": 4, "shift": self.ShiftDirection.EARLIER},  # Fri
            AssignmentType.EXAM: {"preferred_day": 3, "shift": self.ShiftDirection.EARLIER},  # Thu
            AssignmentType.DISCUSSION: {
                "preferred_day": 2,
                "shift": self.ShiftDirection.EARLIER,
            },  # Wed
            AssignmentType.PROJECT: {
                "preferred_day": 4,
                "shift": self.ShiftDirection.EARLIER,
            },  # Fri
        }

    def _holidays_as_dates(self) -> list[datetime]:
        """Flatten holidays from SemesterCalendar into a list of datetimes."""
        holidays: list[datetime] = []
        try:
            for h in self.calendar.get_holidays():  # type: ignore[union-attr]
                if "date" in h:
                    holidays.append(h["date"])  # already a datetime
                elif "start" in h and "end" in h:
                    cur = h["start"]
                    while cur <= h["end"]:
                        holidays.append(cur)
                        cur = cur + timedelta(days=1)
        except Exception:
            return []
        return holidays

    def is_holiday(self, date: datetime) -> bool:
        """Return True if the given date falls on a holiday."""
        d0 = date.replace(hour=0, minute=0, second=0, microsecond=0)
        return any(d0.date() == h.date() for h in self._holidays_as_dates())

    def apply_rules(
        self, label: str, week_start_iso: str, holidays: list[str], *, is_assessment: bool
    ) -> str:
        """Convenience wrapper to choose weekday, apply shifts, and format a due label.

        Returns a string like "(due Wed 09/03)".
        """
        wd = self.choose_due_weekday(label, is_assessment=is_assessment)
        wd, add = self.apply_holiday_shift(wd, holidays, label, is_assessment)
        return self.format_due(week_start_iso, wd, add)

    def apply_date_rules(
        self, date: datetime, assignment_type: AssignmentType = AssignmentType.HOMEWORK
    ) -> datetime:
        """Apply date rules to produce a valid due date.

        - No weekend due dates
        - Holiday shifting (direction based on assignment type)
        - Deterministic outcome for given (date, type)
        """
        prefs = self._type_preferences().get(
            assignment_type, {"shift": self.ShiftDirection.EARLIER}
        )
        direction: DateRules.ShiftDirection = prefs.get("shift", self.ShiftDirection.EARLIER)

        # Weekend handling
        if self.is_weekend(date):
            date = self.shift_from_weekend(date, direction=direction)

        # Holiday handling
        if self.is_holiday(date):
            date = self.shift_for_holiday(date, direction=direction)

        # Safety: ensure we never return a weekend or holiday
        if self.is_weekend(date) or self.is_holiday(date):
            for delta in range(1, 8):
                earlier = date - timedelta(days=delta)
                later = date + timedelta(days=delta)
                if not self.is_weekend(earlier) and not self.is_holiday(earlier):
                    return earlier
                if not self.is_weekend(later) and not self.is_holiday(later):
                    return later
        return date

    @staticmethod
    def is_weekend(date: datetime) -> bool:
        """Check if date falls on weekend (Saturday=5, Sunday=6)."""
        return date.weekday() >= 5

    def shift_from_weekend(
        self, date: datetime, direction: str | DateRules.ShiftDirection = "before"
    ) -> datetime:
        """Shift date away from weekend.

        Args:
            date: Date to shift
            direction: "before"/"after" or ShiftDirection

        Returns:
            Shifted date
        """
        # Normalize direction
        dir_key = (
            direction
            if isinstance(direction, str)
            else ("before" if direction == self.ShiftDirection.EARLIER else "after")
        )

        if dir_key == "before":
            # Shift to Friday
            if date.weekday() == 5:  # Saturday -> Friday
                shifted = date - timedelta(days=1)
                self.shift_log.append(
                    self.DateShift(date, shifted, "Weekend shift", "no_weekend_due_dates")
                )
                return shifted
            elif date.weekday() == 6:  # Sunday -> Friday
                shifted = date - timedelta(days=2)
                self.shift_log.append(
                    self.DateShift(date, shifted, "Weekend shift", "no_weekend_due_dates")
                )
                return shifted
        else:  # direction == "after"
            # Shift to Monday
            if date.weekday() == 5:  # Saturday -> Monday
                shifted = date + timedelta(days=2)
                self.shift_log.append(
                    self.DateShift(date, shifted, "Weekend shift", "no_weekend_due_dates")
                )
                return shifted
            elif date.weekday() == 6:  # Sunday -> Monday
                shifted = date + timedelta(days=1)
                self.shift_log.append(
                    self.DateShift(date, shifted, "Weekend shift", "no_weekend_due_dates")
                )
                return shifted

        return date

    @staticmethod
    def choose_due_weekday(label: str, is_assessment: bool = False) -> int:
        label_lower = label.lower()
        if not is_assessment:
            if (
                "discussion" in label_lower
                or label_lower.startswith("bb")
                or "blackboard" in label_lower
            ):
                return 2  # Wed
            return 4  # Fri default
        if "quiz" in label_lower:
            return 4  # Fri
        if "exam" in label_lower or "midterm" in label_lower or "test" in label_lower:
            return 3  # Thu
        return 4

    @staticmethod
    def apply_holiday_shift(
        weekday: int, holidays: list[str], label: str, is_assessment: bool
    ) -> tuple[int, int]:
        add_days = 0
        joined = ", ".join(holidays)
        if "Fall Break" in joined and weekday in (3, 4):  # Thu/Fri
            label_lower = label.lower()
            if is_assessment and (
                "quiz" in label_lower
                or "exam" in label_lower
                or "test" in label_lower
                or "midterm" in label_lower
            ):
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

    # ---- Extended helpers for builders/tests ----
    def shift_for_holiday(
        self, date: datetime, direction: str | DateRules.ShiftDirection = "before"
    ) -> datetime:
        """Shift dates that fall on holidays, skipping weekends.

        Uses the given direction as the primary vector; falls back to the
        opposite direction if needed to find a valid date within a week.
        """
        if not self.is_holiday(date):
            return date

        dir_key = (
            direction
            if isinstance(direction, str)
            else ("after" if direction == self.ShiftDirection.LATER else "before")
        )

        original = date
        step = 1 if dir_key == "after" else -1
        shifted = date

        attempts = 0
        while attempts < 7 and (self.is_holiday(shifted) or self.is_weekend(shifted)):
            shifted = shifted + timedelta(days=step)
            attempts += 1

        if attempts >= 7:
            step = -step
            shifted = date
            attempts = 0
            while attempts < 7 and (self.is_holiday(shifted) or self.is_weekend(shifted)):
                shifted = shifted + timedelta(days=step)
                attempts += 1

        if shifted != original:
            self.shift_log.append(
                self.DateShift(original, shifted, "Holiday accommodation", "holiday_shift_policy")
            )

        return shifted

    def get_preferred_day(self, assignment_type: AssignmentType, week_start: datetime) -> datetime:
        """Return preferred due date for the given assignment type within a week.

        week_start is expected to be the Monday of the given week.
        """
        prefs = self._type_preferences().get(assignment_type, {})
        preferred_day = int(prefs.get("preferred_day", 4))  # default Friday
        target = week_start + timedelta(days=preferred_day)
        return self.apply_date_rules(target, assignment_type)

    def validate_schedule(self, dates: list[datetime]) -> list[str]:
        """Validate a list of dates, returning human-readable error strings."""
        errors: list[str] = []
        for d in dates:
            if self.is_weekend(d):
                errors.append(f"Date {d.strftime('%Y-%m-%d')} falls on weekend")
            if self.is_holiday(d):
                errors.append(f"Date {d.strftime('%Y-%m-%d')} falls on holiday")
        return errors

    def get_shift_report(self) -> dict[str, Any]:
        """Summarize shift provenance into a simple report dict."""
        return {
            "total_shifts": len(self.shift_log),
            "weekend_shifts": sum(1 for s in self.shift_log if "Weekend" in s.reason),
            "holiday_shifts": sum(1 for s in self.shift_log if "Holiday" in s.reason),
            "shifts": [
                {
                    "original": s.original.isoformat(),
                    "shifted": s.shifted.isoformat(),
                    "reason": s.reason,
                    "rule": s.rule,
                }
                for s in self.shift_log
            ],
        }
