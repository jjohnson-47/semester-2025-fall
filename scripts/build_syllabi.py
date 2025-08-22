#!/usr/bin/env python3
"""Syllabus builder: render course data with Jinja2 templates.

Loads course, global, and instructor data and renders Markdown/HTML syllabi
into ``build/syllabi``. Optionally attempts PDF generation using WeasyPrint or
Pandoc if available in the environment.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.utils.jinja_env import create_jinja_env
from scripts.utils.semester_calendar import SemesterCalendar

# Load environment variables from .env if it exists
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                os.environ[key] = value.strip('"')


class SyllabusBuilder:
    """Build course syllabi from templates and data.

    Parameters
    - template_dir: root directory for Jinja2 templates.
    - output_dir: destination directory for rendered files.
    """

    def __init__(self, template_dir: str = "templates", output_dir: str = "build/syllabi"):
        self.template_dir = Path(template_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.env = create_jinja_env(str(self.template_dir))
        self.calendar = SemesterCalendar()

    def load_course_data(self, course_code: str) -> dict[str, Any]:
        """Load all JSON data for a course.

        Parameters
        - course_code: e.g., ``MATH221``.

        Returns
        - dict: combined context used by templates (course/global/instructor/calendar).
        """
        course_dir = Path(f"content/courses/{course_code}")
        if not course_dir.exists():
            raise FileNotFoundError(f"Course directory not found: {course_dir}")

        data = {
            "course_code": course_code,
            "course_number": course_code,
            "semester": os.getenv("SEMESTER_NAME", "Fall 2025"),
            "year": 2025,
        }

        # Load all JSON files in course directory
        for json_file in course_dir.glob("*.json"):
            with open(json_file, encoding="utf-8") as f:
                key = json_file.stem
                data[key] = json.load(f)

        # Load global data
        self._load_global_data(data)

        # Load instructor profile
        self._load_instructor_data(data)

        # Map course meta to top-level header fields
        meta = data.get("course_meta", {}) if isinstance(data.get("course_meta"), dict) else {}
        data["course_crn"] = meta.get("course_crn", data.get("course_crn"))
        data["course_credits"] = meta.get("course_credits", data.get("course_credits"))
        data["course_section"] = meta.get("section", os.getenv(f"{course_code}_SECTION"))
        data["course_format"] = meta.get("format", os.getenv(f"{course_code}_FORMAT"))

        # Add calendar data
        data["calendar"] = self.calendar.get_course_calendar(course_code)

        # Add course-specific names
        data["course_name_full"] = os.getenv(f"{course_code}_FULL", "")
        data["course_name_short"] = os.getenv(f"{course_code}_SHORT", "")

        return data

    def _load_global_data(self, data: dict[str, Any]) -> None:
        """Load global policies and configuration into ``data``.

        Scans ``global/`` and ``variables/`` for JSON files and attaches their
        contents using ``global_<name>`` and ``var_<name>`` keys respectively.
        """
        global_dir = Path("global")
        if global_dir.exists():
            for json_file in global_dir.glob("*.json"):
                with open(json_file, encoding="utf-8") as f:
                    key = f"global_{json_file.stem}"
                    data[key] = json.load(f)

        # Load variables
        variables_dir = Path("variables")
        if variables_dir.exists():
            for json_file in variables_dir.glob("*.json"):
                with open(json_file, encoding="utf-8") as f:
                    key = f"var_{json_file.stem}"
                    data[key] = json.load(f)

    def _load_instructor_data(self, data: dict[str, Any]) -> None:
        """Load instructor profile into ``data``.

        If ``profiles/instructor.json`` is missing, populates a minimal profile
        from environment variables.
        """
        instructor_file = Path("profiles/instructor.json")
        if instructor_file.exists():
            with open(instructor_file, encoding="utf-8") as f:
                data["instructor"] = json.load(f)
        else:
            # Use environment variables as fallback
            data["instructor"] = {
                "name": os.getenv("INSTRUCTOR_NAME", "Jeffrey Johnson"),
                "email": os.getenv("INSTRUCTOR_EMAIL", "jjohnson47@alaska.edu"),
                "office": os.getenv("INSTRUCTOR_OFFICE", "Ward Building"),
                "phone": os.getenv("INSTRUCTOR_PHONE", ""),
                "title": os.getenv("INSTRUCTOR_TITLE", "Instructor"),
            }

    def build_syllabus(self, course_code: str) -> dict[str, str]:
        """Build syllabus for a single course.

        Returns
        - dict: mapping of artifact types to file paths (``html``, ``markdown``,
          and optionally ``pdf`` if available).
        """
        print(f"Building syllabus for {course_code}...")

        # Load data
        data = self.load_course_data(course_code)

        # Generate HTML
        html_template = self.env.get_template("syllabus.html.j2")
        html_output = html_template.render(**data)
        html_path = self.output_dir / f"{course_code}.html"
        html_path.write_text(html_output, encoding="utf-8")

        # Generate Markdown
        md_template = self.env.get_template("syllabus.md.j2")
        md_output = md_template.render(**data)
        md_path = self.output_dir / f"{course_code}.md"
        md_path.write_text(md_output, encoding="utf-8")

        # Generate PDF if enabled
        pdf_path = None
        if os.getenv("BUILD_PDF", "true").lower() == "true":
            pdf_path = self._generate_pdf(html_path, course_code)

        return {
            "html": str(html_path),
            "markdown": str(md_path),
            "pdf": str(pdf_path) if pdf_path else "",
        }

    def _generate_pdf(self, html_path: Path, course_code: str) -> Path | None:
        """Generate a PDF from an HTML file using WeasyPrint or Pandoc.

        Returns
        - Path | None: path to the generated PDF, or None if PDF generation is
          not available.
        """
        pdf_path = self.output_dir / f"{course_code}.pdf"

        try:
            # Try weasyprint first
            from weasyprint import HTML

            HTML(filename=str(html_path)).write_pdf(str(pdf_path))
            return pdf_path
        except ImportError:
            # Fall back to pandoc if available
            try:
                import pypandoc

                pypandoc.convert_file(
                    str(html_path),
                    "pdf",
                    outputfile=str(pdf_path),
                    extra_args=["--pdf-engine=xelatex"],
                )
                return pdf_path
            except (ImportError, RuntimeError):
                print("Warning: PDF generation skipped (install weasyprint or pandoc)")
                return None

    def build_all(self, courses: list[str] | None = None) -> dict[str, dict[str, str]]:
        """Build syllabi for all courses.

        Parameters
        - courses: optional subset of course codes. If omitted, defaults to the
          standard set.
        """
        if courses is None:
            courses = ["MATH221", "MATH251", "STAT253"]

        results = {}
        for course in courses:
            try:
                results[course] = self.build_syllabus(course)
                print(f"✓ {course} syllabus generated")
            except Exception as e:
                print(f"✗ Error building {course}: {e}")
                results[course] = {"error": str(e)}

        return results


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Build course syllabi")
    parser.add_argument("--course", help="Build specific course (e.g., MATH221)")
    parser.add_argument("--output", default="build/syllabi", help="Output directory")
    parser.add_argument("--template-dir", default="templates", help="Template directory")
    parser.add_argument("--ci", action="store_true", help="CI mode (fail on error)")

    args = parser.parse_args()

    builder = SyllabusBuilder(template_dir=args.template_dir, output_dir=args.output)

    try:
        if args.course:
            results = {args.course: builder.build_syllabus(args.course)}
        else:
            results = builder.build_all()

        # Check for errors in CI mode
        if args.ci:
            errors = [c for c, r in results.items() if "error" in r]
            if errors:
                print(f"Build failed for: {', '.join(errors)}")
                sys.exit(1)

        print(f"\nSyllabi built in: {args.output}/")

    except Exception as e:
        print(f"Build failed: {e}")
        if args.ci:
            sys.exit(1)
        raise


if __name__ == "__main__":
    main()
