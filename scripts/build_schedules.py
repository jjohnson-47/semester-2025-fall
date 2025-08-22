#!/usr/bin/env python3
"""Schedule builder: align course plans to the academic calendar.

Reads each course's ``content/courses/<COURSE>/schedule.json`` and generates
Markdown schedules in ``build/schedules/`` with week ranges aligned to the
academic calendar. Assigns student-friendly due days by item type and shifts
around major holidays (e.g., Fall Break). No weekend deadlines are produced.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.utils.semester_calendar import SemesterCalendar


def _parse_date(date_str: str) -> datetime:
    return datetime.strptime(date_str, "%Y-%m-%d")


class ScheduleBuilder:
    """Build course schedules aligned to the semester calendar.

    Parameters
    - output_dir: destination directory for Markdown outputs.
    - calendar: optional injected calendar instance (primarily for tests).
    - content_root: project root (for tests); defaults to current directory.
    """

    def __init__(
        self,
        output_dir: str = "build/schedules",
        calendar: SemesterCalendar | None = None,
        content_root: Path | None = None,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.calendar = calendar or SemesterCalendar()
        self.content_root = Path(".") if content_root is None else Path(content_root)

    def _load_course_schedule(self, course_code: str) -> dict[str, Any] | None:
        """Load a course's schedule JSON if available.

        Parameters
        - course_code: e.g., ``MATH221``.

        Returns
        - dict | None: parsed schedule or None on missing/unreadable file.
        """
        schedule_path = self.content_root / f"content/courses/{course_code}/schedule.json"
        if not schedule_path.exists():
            return None
        try:
            data: dict[str, Any] | None = json.loads(schedule_path.read_text(encoding="utf-8"))
            return data
        except Exception:
            return None

    def _format_dates_range(self, start: str, end_friday: str) -> str:
        """Format a Monday–Sunday date range for display (e.g., ``Sep 02 - Sep 08``)."""
        start_dt = _parse_date(start)
        end_dt = _parse_date(end_friday) + timedelta(days=2)  # align to Sunday
        start_str = start_dt.strftime("%b %d")
        end_str = end_dt.strftime("%b %d")
        return f"{start_str} - {end_str}"

    def _choose_due_weekday(self, label: str, is_assessment: bool = False) -> int:
        """Pick a due weekday index (Mon=0..Sun=6) using heuristics.

        - Discussions / BB tasks → Wed (2)
        - Quizzes → Fri (4)
        - Exams / Midterms / Tests → Thu (3)
        - Homework / platforms → Fri (4)
        """
        label_lower = label.lower()
        if not is_assessment:
            if "discussion" in label_lower or label_lower.startswith("bb") or "bb" in label_lower:
                return 2  # Wed
            # homework/platforms default to Friday
            return 4  # Fri
        # assessments
        if "quiz" in label_lower:
            return 4  # Fri
        if "exam" in label_lower or "midterm" in label_lower or "test" in label_lower:
            return 3  # Thu
        return 4

    def _apply_holiday_shift(
        self, weekday: int, holidays: list[str], label: str, is_assessment: bool
    ) -> tuple[int, int]:
        """Shift due weekday to avoid major breaks when reasonable.

        - If Fall Break present:
          - Exams/Quizzes scheduled Thu/Fri shift to Wed of same week.
          - Homework (Fri) shifts to next Monday.
        Returns a tuple of (weekday, extra_days).
        """
        add_days = 0
        if holidays:
            joined = ", ".join(holidays)
            if "Fall Break" in joined and weekday in (3, 4):  # Thu/Fri
                label_lower = label.lower()
                if is_assessment and (
                    "quiz" in label_lower
                    or "exam" in label_lower
                    or "test" in label_lower
                    or "midterm" in label_lower
                ):
                    return 2, 0  # shift to Wed same week
                # assignments/homework -> shift to next Monday
                return 0, 7
        # Avoid weekend due dates in any case
        if weekday in (5, 6):
            # Move Sunday to Monday, Saturday to Friday
            return (0 if weekday == 6 else 4), add_days
        return weekday, add_days

    def _format_due(self, week_start: str, weekday: int, add_days: int = 0) -> str:
        start_dt = _parse_date(week_start)
        due_dt = start_dt + timedelta(days=weekday + add_days)
        day_label = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][weekday]
        return f"(due {day_label} {due_dt.strftime('%m/%d')})"

    def build_schedule(self, course_code: str, default_due_day: str = "Sun") -> str:
        """Build schedule for a single course by aligning to calendar weeks.

        Parameters
        - course_code: e.g., ``MATH251``.
        - default_due_day: retained for backward compatibility; the builder
          now emits concrete due dates instead of this label.

        Returns
        - str: path to the generated Markdown file.
        """
        print(f"Building schedule for {course_code}...")

        weeks = self.calendar.get_weeks()
        course_schedule = self._load_course_schedule(course_code)

        # Build static header using calendar
        dates = self.calendar.get_semester_dates()
        header = [
            f"# {course_code} - Fall 2025 Schedule",
            "",
            "## Important Dates",
            "",
            f"- **Classes Begin:** {dates['start'].strftime('%B %d, %Y')}",
            f"- **Add/Drop Deadline:** {dates['add_drop'].strftime('%B %d, %Y')}",
            f"- **Withdrawal Deadline:** {dates['withdrawal'].strftime('%B %d, %Y')}",
            f"- **Finals Week:** {dates['finals_start'].strftime('%B %d, %Y')} - {dates['finals_end'].strftime('%B %d, %Y')}",
            "",
            "## Weekly Schedule",
            "",
            "| Week | Dates | Topics | Assignments | Assessments |",
            "|------|-------|--------|-------------|-------------|",
        ]

        rows: list[str] = []
        instruction_weeks = [w for w in weeks if not w.get("is_finals")]

        if course_schedule and "weeks" in course_schedule:
            planned_weeks: list[dict[str, Any]] = course_schedule["weeks"]
            count = min(len(planned_weeks), len(instruction_weeks))
            for idx in range(count):
                pw = planned_weeks[idx]
                cw = instruction_weeks[idx]
                date_range = self._format_dates_range(cw["start"], cw["end"])
                holidays = f" ({', '.join(cw['holidays'])})" if cw.get("holidays") else ""
                topic = pw.get("topic", f"Week {idx + 1} Content")
                # Assignments with due dates
                assignments: list[str] = []
                for item in pw.get("assignments", []):
                    wd = self._choose_due_weekday(item, is_assessment=False)
                    wd, add = self._apply_holiday_shift(wd, cw.get("holidays", []), item, False)
                    assignments.append(f"{item} {self._format_due(cw['start'], wd, add)}")
                # Assessments with due dates where applicable
                assessments: list[str] = []
                for a in pw.get("assessments", []):
                    wd = self._choose_due_weekday(a, is_assessment=True)
                    wd, add = self._apply_holiday_shift(wd, cw.get("holidays", []), a, True)
                    assessments.append(f"{a} {self._format_due(cw['start'], wd, add)}")
                rows.append(
                    f"| {idx + 1} | {date_range}{holidays} | {topic} | {', '.join(assignments)} | {', '.join(assessments)} |"
                )
        else:
            # Fallback generic schedule if no course schedule available
            for i, cw in enumerate(instruction_weeks[:16], 1):
                date_range = self._format_dates_range(cw["start"], cw["end"])
                holidays = f" ({', '.join(cw['holidays'])})" if cw.get("holidays") else ""
                rows.append(
                    f"| {i} | {date_range}{holidays} | Week {i} Content | HW {i} (due {default_due_day}) | |"
                )

        # Finals row(s)
        finals_weeks = [w for w in weeks if w.get("is_finals")]
        if finals_weeks:
            first = finals_weeks[0]
            date_range = self._format_dates_range(first["start"], first["end"])  # end->Sunday
            finals_topic = "Final Exam"
            finals_assessments = []
            if course_schedule and course_schedule.get("finals"):
                finals_topic = course_schedule["finals"].get("topic", finals_topic)
                finals_assessments = course_schedule["finals"].get("assessments", [])
            rows.append(
                f"| Finals | {date_range} | {finals_topic} |  | {', '.join(finals_assessments)} |"
            )

        # Write file
        schedule_text = "\n".join(header + rows)
        output_file = self.output_dir / f"{course_code}_schedule.md"
        output_file.write_text(schedule_text, encoding="utf-8")
        return str(output_file)

    def build_all(self, courses: list[str] | None = None) -> None:
        """Build schedules for all courses in ``courses`` (or the defaults)."""
        if courses is None:
            courses = ["MATH221", "MATH251", "STAT253"]

        for course in courses:
            self.build_schedule(course)
            print(f"✓ {course} schedule generated")


def main() -> None:
    """CLI entry point for the schedule builder."""
    parser = argparse.ArgumentParser(description="Build course schedules")
    parser.add_argument("--course", help="Build specific course")
    parser.add_argument("--output", default="build/schedules", help="Output directory")
    parser.add_argument("--ci", action="store_true", help="CI mode")

    args = parser.parse_args()

    builder = ScheduleBuilder(output_dir=args.output)

    if args.course:
        builder.build_schedule(args.course)
    else:
        builder.build_all()

    print(f"\nSchedules built in: {args.output}/")


if __name__ == "__main__":
    main()
