"""Ported tests for DateRules weekend/policy enforcement and provenance.

Adapted from feat/date-authority branch to current DateRules API.
"""

from __future__ import annotations

from datetime import datetime

from scripts.rules.dates import DateRules
from scripts.rules.models import AssignmentType


def test_weekend_detection_basics() -> None:
  rules = DateRules()
  assert not rules.is_weekend(datetime(2025, 9, 5))  # Friday
  assert rules.is_weekend(datetime(2025, 9, 6))  # Saturday
  assert rules.is_weekend(datetime(2025, 9, 7))  # Sunday


def test_shift_from_weekend_directions() -> None:
  rules = DateRules()
  # Earlier (to Friday)
  sat = datetime(2025, 9, 6)
  shifted = rules.shift_from_weekend(sat, DateRules.ShiftDirection.EARLIER)
  assert shifted == datetime(2025, 9, 5)
  # Later (to Monday)
  sun = datetime(2025, 9, 7)
  shifted2 = rules.shift_from_weekend(sun, DateRules.ShiftDirection.LATER)
  assert shifted2 == datetime(2025, 9, 8)


def test_apply_date_rules_weekend_never_returns_weekend() -> None:
  rules = DateRules()
  sat = datetime(2025, 9, 6)
  result = rules.apply_date_rules(sat, AssignmentType.HOMEWORK)
  assert not rules.is_weekend(result)
  assert result.weekday() == 4  # Friday


def test_preferred_days_for_types() -> None:
  rules = DateRules()
  week_start = datetime(2025, 9, 1)  # Monday
  # Homework -> Friday
  hw = rules.get_preferred_day(AssignmentType.HOMEWORK, week_start)
  assert hw == datetime(2025, 9, 5)
  # Exam -> Thursday
  exam = rules.get_preferred_day(AssignmentType.EXAM, week_start)
  assert exam == datetime(2025, 9, 4)


def test_shift_log_provenance_records() -> None:
  rules = DateRules()
  sat = datetime(2025, 9, 6)
  rules.shift_from_weekend(sat)
  assert len(rules.shift_log) == 1
  rec = rules.shift_log[0]
  assert rec.original == sat
  assert rec.shifted == datetime(2025, 9, 5)
  assert "Weekend" in rec.reason and rec.rule == "no_weekend_due_dates"


def test_shift_report_summary_counts() -> None:
  rules = DateRules()
  rules.shift_from_weekend(datetime(2025, 9, 6))
  rules.shift_from_weekend(datetime(2025, 9, 7))
  summary = rules.get_shift_report()
  assert summary["total_shifts"] == 2
  assert summary["weekend_shifts"] == 2
