#!/usr/bin/env python3
from __future__ import annotations

from scripts.rules.dates import DateRules


def test_choose_due_weekday_assignments_and_assessments() -> None:
    # Assignments
    assert DateRules.choose_due_weekday("MyOpenMath: HW 1") == 4  # Fri
    assert DateRules.choose_due_weekday("Blackboard Discussion: Week 1") == 2  # Wed
    # Assessments
    assert DateRules.choose_due_weekday("Quiz #1", is_assessment=True) == 4
    assert DateRules.choose_due_weekday("Exam #1", is_assessment=True) == 3


def test_holiday_shift_fall_break() -> None:
    # Assessments on Thu/Fri during Fall Break move to Wed
    wd, add = DateRules.apply_holiday_shift(3, ["Fall Break"], "Exam #1", True)
    assert (wd, add) == (2, 0)
    wd, add = DateRules.apply_holiday_shift(4, ["Fall Break"], "Quiz #1", True)
    assert (wd, add) == (2, 0)

    # Assignments on Fri move to next Mon
    wd, add = DateRules.apply_holiday_shift(4, ["Fall Break"], "Homework 3", False)
    assert (wd, add) == (0, 7)


def test_weekend_avoidance() -> None:
    wd, add = DateRules.apply_holiday_shift(5, [], "anything", False)
    assert (wd, add) == (4, 0)  # Sat -> Fri
    wd, add = DateRules.apply_holiday_shift(6, [], "anything", False)
    assert (wd, add) == (0, 0)  # Sun -> Mon


def test_format_due_output() -> None:
    s = DateRules.format_due("2025-09-01", 2, 0)  # Wed of that week
    assert s.startswith("(due Wed ") and s.endswith(")")

