#!/usr/bin/env python3
"""Scaffold course content JSON files for a given course code.

Creates `content/courses/<COURSE>/` and writes placeholder JSON files
used by the syllabus and schedule builders.

Usage:
  uv run python scripts/utils/scaffold_course.py --course MATH221

Notes:
  - Existing files are not overwritten unless `--force` is provided.
  - The generated files aim for compatibility with templates/syllabus.*.j2
    and can be customized after creation.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ScaffoldFile:
    """Represents a single file to scaffold with its default content."""

    name: str
    content: dict


def default_scaffold() -> list[ScaffoldFile]:
    """Return the default set of course JSON files and their content."""
    return [
        ScaffoldFile(
            "course_meta.json",
            {"course_crn": "TBD", "course_credits": 3},
        ),
        ScaffoldFile("course_description.json", {"text": "Course description to be provided."}),
        ScaffoldFile("course_prerequisites.json", {"text": ""}),
        ScaffoldFile("instructional_goals.json", {"goals": []}),
        ScaffoldFile("student_outcomes.json", {"outcomes": []}),
        ScaffoldFile(
            "required_textbook.json",
            {"title": "", "author": "", "edition": "", "isbn": "", "notes": ""},
        ),
        ScaffoldFile(
            "calculators_and_technology.json",
            {"requirements": "- Reliable internet\n- Modern web browser\n"},
        ),
        ScaffoldFile(
            "evaluation_tools.json",
            {
                "categories": [
                    {"name": "Homework", "weight": 40},
                    {"name": "Quizzes/Exams", "weight": 40},
                    {"name": "Participation", "weight": 20},
                ]
            },
        ),
        ScaffoldFile(
            "grading_policy.json",
            {
                "scale": [
                    {"letter": "A", "range": "90-100%", "points": 900},
                    {"letter": "B", "range": "80-89%", "points": 800},
                    {"letter": "C", "range": "70-79%", "points": 700},
                    {"letter": "D", "range": "60-69%", "points": 600},
                    {"letter": "F", "range": "< 60%", "points": 0},
                ]
            },
        ),
        ScaffoldFile("class_policies.json", {"late_work": "Late work policy to be defined."}),
        ScaffoldFile("safety.json", {"text": ""}),
        ScaffoldFile("rsi.json", {"text": ""}),
    ]


def write_json(path: Path, data: dict, force: bool) -> bool:
    """Write JSON to `path` if not exists or `force` is True. Returns True if written."""
    if path.exists() and not force:
        return False
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    return True


def scaffold_course(course_code: str, force: bool = False) -> list[tuple[str, str]]:
    """Create course directory and scaffold files. Returns list of (path, action)."""
    course_dir = Path("content") / "courses" / course_code
    course_dir.mkdir(parents=True, exist_ok=True)

    actions: list[tuple[str, str]] = []
    for spec in default_scaffold():
        file_path = course_dir / spec.name
        written = write_json(file_path, spec.content, force)
        actions.append((str(file_path), "created" if written else "skipped"))

    return actions


def main() -> None:
    parser = argparse.ArgumentParser(description="Scaffold course content")
    parser.add_argument("--course", required=True, help="Course code, e.g., MATH221")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    args = parser.parse_args()

    actions = scaffold_course(args.course, args.force)
    print(f"Scaffold for {args.course}:")
    for path, action in actions:
        print(f"  - {action}: {path}")


if __name__ == "__main__":
    main()
