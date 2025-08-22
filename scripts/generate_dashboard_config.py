#!/usr/bin/env python3
"""
Generate dashboard configuration from existing course data.
Creates courses.json for the dashboard system.
"""

import json
import os
from datetime import datetime
from pathlib import Path


def main():
    """Generate dashboard configuration."""

    # Read academic calendar
    calendar_path = Path("academic-calendar.json")
    if calendar_path.exists():
        with open(calendar_path) as f:
            calendar = json.load(f)
    else:
        print("Warning: academic-calendar.json not found")
        calendar = {}

    # Extract Fall 2025 dates
    fall_2025 = calendar.get("semesters", {}).get("fall_2025", {})

    courses_data = {
        "semester": "2025-fall",
        "timezone": "America/Anchorage",
        "important_dates": {
            "first_day": fall_2025.get("start_date", "2025-08-25"),
            "last_day": fall_2025.get("end_date", "2025-12-13"),
            "finals_window": f"{fall_2025.get('finals_start', '2025-12-08')}..{fall_2025.get('finals_end', '2025-12-13')}",
            "drop_deadline": fall_2025.get("critical_deadlines", {})
            .get("add_drop", {})
            .get("date", "2025-09-05"),
            "withdrawal_deadline": fall_2025.get("critical_deadlines", {})
            .get("withdrawal_deadline", {})
            .get("date", "2025-10-31"),
        },
        "courses": [],
    }

    # Course configurations from fall-2025-courses.md
    course_configs = [
        ("MATH221", "Applied Calculus for Managerial and Social Sciences", "74645", 3),
        ("MATH251", "Calculus I", "74647", 4),
        ("STAT253", "Applied Statistics for the Sciences", "74688", 4),
    ]

    for code, title, crn, credits in course_configs:
        course = {
            "code": code,
            "title": title,
            "crn": crn,
            "credits": credits,
            "modality": "online",
            "section": "901",
            "weeks": 16,  # Fall 2025 is 16 weeks
            "blackboard": {
                "course_id": f"2025-FALL-{code}-901",
                "copy_from_id": f"2024-FALL-{code}-901",
                "links": {
                    "shell": f"https://blackboard.alaska.edu/ultra/courses/_123456_{code}_1",
                    "grade_center": "https://blackboard.alaska.edu/webapps/gradebook2/controller",
                },
            },
        }

        # Read evaluation_tools.json if exists
        eval_path = Path(f"content/courses/{code}/evaluation_tools.json")
        if eval_path.exists():
            with open(eval_path) as f:
                course["evaluation"] = json.load(f)
        else:
            # Default evaluation structure
            course["evaluation"] = {
                "categories": [
                    {"name": "Homework", "weight": 20},
                    {"name": "Quizzes", "weight": 15},
                    {"name": "Midterm Exams", "weight": 30},
                    {"name": "Final Exam", "weight": 25},
                    {"name": "Participation", "weight": 10},
                ]
            }

        # Read course description if exists
        desc_path = Path(f"content/courses/{code}/course_description.json")
        if desc_path.exists():
            with open(desc_path) as f:
                desc_data = json.load(f)
                course["description"] = desc_data.get("text", "")

        courses_data["courses"].append(course)

    # Write dashboard configuration
    os.makedirs("dashboard/state", exist_ok=True)
    output_path = Path("dashboard/state/courses.json")

    with open(output_path, "w") as f:
        json.dump(courses_data, f, indent=2)

    print("✓ Generated dashboard/state/courses.json")
    print(f"  - Semester: {courses_data['semester']}")
    print(f"  - Courses: {', '.join(c['code'] for c in courses_data['courses'])}")
    print(f"  - First day: {courses_data['important_dates']['first_day']}")
    print(f"  - Last day: {courses_data['important_dates']['last_day']}")

    # Also create an empty tasks.json if it doesn't exist
    tasks_path = Path("dashboard/state/tasks.json")
    if not tasks_path.exists():
        initial_tasks = {
            "tasks": [],
            "metadata": {
                "version": "1.0",
                "created": datetime.now().isoformat(),
                "semester": "2025-fall",
            },
        }
        with open(tasks_path, "w") as f:
            json.dump(initial_tasks, f, indent=2)
        print("✓ Created initial dashboard/state/tasks.json")


if __name__ == "__main__":
    main()
