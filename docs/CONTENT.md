Content Creation Guide
======================

Overview
--------

- Purpose: Define how to add and manage course content for syllabi and schedules.
- Location: Course-specific JSON files live under `content/courses/<COURSE>/`.
- Templates: Rendered via `templates/syllabus.html.j2` and `templates/syllabus.md.j2`.

Quick Start
-----------

- Scaffold files: `make scaffold COURSE=MATH221`
- Edit JSON files under `content/courses/MATH221/` with real content.
- Validate JSON: `make validate`
- Build syllabi: `make syllabi` (outputs to `build/syllabi/`)
- Build schedules: `make schedules` (outputs to `build/schedules/`)

Course Directory Layout
-----------------------

- `course_meta.json`: Basic metadata like CRN and credits.
- `course_description.json`: `{ "text": "..." }` course description.
- `course_prerequisites.json`: `{ "text": "..." }` prerequisites.
- `instructional_goals.json`: `{ "goals": ["...", "..."] }` course goals.
- `student_outcomes.json`: `{ "outcomes": ["...", "..."] }` outcomes.
- `required_textbook.json`: `title`, `author`, `edition`, `isbn`, `notes`.
- `calculators_and_technology.json`: `{ "requirements": "markdown list" }`.
- `evaluation_tools.json`: `{ "categories": [{"name": "...", "weight": 40}, ...] }`.
- `grading_policy.json`: `{ "scale": [{"letter": "A", "range": "90-100%", "points": 900}, ...] }`.
- `class_policies.json`: `{ "late_work": "..." }`.
- `safety.json` / `rsi.json`: `{ "text": "..." }` optional sections.

Global Data
-----------

- `profiles/instructor.json` (optional): Overrides environment defaults used by builders.
- `global/*.json` and `variables/*.json`: Included automatically for shared policies/config.

Best Practices
--------------

- Validate often: run `make validate` to catch JSON syntax issues early.
- Keep weights totaling 100 in `evaluation_tools.json`.
- Use clear, concise text; markdown is supported in some fields.
- Avoid secrets in content; use environment variables for sensitive config.

Advanced
--------

- Environment vars for course names: set `MATH221_FULL` and `MATH221_SHORT` in `.env`.
- PDF generation: install `weasyprint` or `pandoc` to enable PDF outputs.
- Schemas: Add JSON Schemas under `scripts/utils/schema/` to enforce structure when ready.
