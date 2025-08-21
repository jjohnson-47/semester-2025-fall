#!/usr/bin/env python3
"""
Build course schedules from calendar and course data.
Generates weekly schedule views for each course.
"""

import json
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.utils.calendar import SemesterCalendar


class ScheduleBuilder:
    """Build course schedules."""
    
    def __init__(self, output_dir: str = "build/schedules"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.calendar = SemesterCalendar()
    
    def build_schedule(self, course_code: str) -> str:
        """Build schedule for a single course."""
        print(f"Building schedule for {course_code}...")
        
        weeks = self.calendar.get_weeks()
        
        # Create markdown schedule
        schedule = [
            f"# {course_code} - Fall 2025 Schedule",
            "",
            "## Important Dates",
            "",
            "- **Classes Begin:** August 25, 2025",
            "- **Add/Drop Deadline:** September 5, 2025",
            "- **Withdrawal Deadline:** October 31, 2025",
            "- **Finals Week:** December 8-13, 2025",
            "",
            "## Weekly Schedule",
            "",
            "| Week | Dates | Topics | Assignments |",
            "|------|-------|--------|-------------|",
        ]
        
        for i, week in enumerate(weeks[:16], 1):
            if week.get('is_finals'):
                schedule.append(f"| Finals | {week['start']} - {week['end']} | Final Exam | |")
            else:
                holidays = f" ({', '.join(week['holidays'])})" if week['holidays'] else ""
                schedule.append(f"| {i} | {week['start']} - {week['end']}{holidays} | Week {i} Content | HW {i} |")
        
        schedule_text = "\n".join(schedule)
        
        # Write to file
        output_file = self.output_dir / f"{course_code}_schedule.md"
        output_file.write_text(schedule_text)
        
        return str(output_file)
    
    def build_all(self, courses=None):
        """Build schedules for all courses."""
        if courses is None:
            courses = ['MATH221', 'MATH251', 'STAT253']
        
        for course in courses:
            self.build_schedule(course)
            print(f"✓ {course} schedule generated")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description='Build course schedules')
    parser.add_argument('--course', help='Build specific course')
    parser.add_argument('--output', default='build/schedules', help='Output directory')
    parser.add_argument('--ci', action='store_true', help='CI mode')
    
    args = parser.parse_args()
    
    builder = ScheduleBuilder(output_dir=args.output)
    
    if args.course:
        builder.build_schedule(args.course)
    else:
        builder.build_all()
    
    print(f"\nSchedules built in: {args.output}/")


if __name__ == '__main__':
    main()