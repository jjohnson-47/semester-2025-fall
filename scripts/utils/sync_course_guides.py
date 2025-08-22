#!/usr/bin/env python3
"""Sync course guide sources into structured course JSON files.

Reads docs/reference/course-guides/<COURSE>*.(md|markdown), extracts exact
language for Course Description, Prerequisites, Instructional Goals, and
Student Learning Outcomes, and writes them into:

- content/courses/<COURSE>/course_description.json
- content/courses/<COURSE>/course_prerequisites.json
- content/courses/<COURSE>/instructional_goals.json
- content/courses/<COURSE>/student_outcomes.json

The script preserves raw guides; it only converts and updates the JSON used by
templates so syllabi render with official wording.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

GUIDES_DIR = Path("docs/reference/course-guides")
COURSES_DIR = Path("content/courses")


SECTION_ALIASES: dict[str, list[str]] = {
    "description": [
        "course description",
        "description",
    ],
    "prerequisites": [
        "prerequisites",
        "prerequisite",
    ],
    "goals": [
        "instructional goals",
        "course goals",
        "instructional objectives",
        "objectives",
        "goals",
    ],
    "outcomes": [
        "required quantitative skills course student learning outcomes",
        "other course specific student learning outcomes",
        "course student learning outcomes",
    ],
}


HEADER_RE = re.compile(r"^(?P<hashes>#{1,6})\s+(?P<title>.+?)\s*$")


@dataclass
class GuideSections:
    description: str | None = None
    prerequisites: str | None = None
    goals: list[str] | None = None
    outcomes: list[str] | None = None


def _is_bullet(line: str) -> bool:
    """Return True if a line looks like a Markdown bullet.

    Supports ``- ``, ``* ``, and numbered bullets like ``1. ``.
    """
    return line.strip().startswith(("-", "*")) or (
        line.strip() and line.strip()[0].isdigit() and "." in line.strip()[:3]
    )


def _normalize_bullets(lines: list[str]) -> list[str]:
    items: list[str] = []
    for ln in lines:
        if not _is_bullet(ln):
            continue
        s = ln.strip()
        s = re.sub(r"^[-*]\s+", "", s)
        s = re.sub(r"^\d+\.\s+", "", s)
        if s:
            items.append(s)
    return items


def _strip_md_formatting(text: str) -> str:
    s = text.strip()
    # remove surrounding bold/italics markers
    s = re.sub(r"^\*\*([^*]+)\*\*$", r"\1", s)
    s = re.sub(r"^\*([^*]+)\*$", r"\1", s)
    s = re.sub(r"^_([^_]+)_$", r"\1", s)
    return s.strip()


UNWANTED_OUTCOME_LINES = {
    "exams",
    "quizzes",
    "in-class exercises",
    "written assignments",
    "projects",
}


def _extract_table_first_column(lines: list[str]) -> list[str]:
    results: list[str] = []
    for ln in lines:
        s = ln.strip()
        if not (s.startswith("|") and s.endswith("|")):
            continue
        # skip header separator rows like |-----|-----|
        if re.match(r"^\|\s*[-: ]+\|", s):
            continue
        # split columns
        cols = [c.strip() for c in s.strip("|").split("|")]
        if cols:
            first = _strip_md_formatting(cols[0])
            if first and "|" not in first:
                results.append(first)
    return results


def _extract_goal_items(block: list[str]) -> list[str]:
    # Prefer bullets; else take clean non-heading lines without trailing colons
    if any(_is_bullet(ln) for ln in block):
        candidates = _normalize_bullets(block)
    else:
        candidates = [ln.strip() for ln in block if ln.strip() and not ln.strip().startswith("#")]
    cleaned: list[str] = []
    for c in candidates:
        t = _strip_md_formatting(c)
        if t.lower().startswith("instructional goals"):
            continue
        if t.endswith(":"):
            continue
        if t:
            cleaned.append(t)
    return cleaned


def _extract_outcome_items(block: list[str]) -> list[str]:
    items: list[str] = []
    # 1) Table first column values
    items.extend(_extract_table_first_column(block))
    # 2) Bullet items
    if any(_is_bullet(ln) for ln in block):
        items.extend(_normalize_bullets(block))
    else:
        items.extend([ln.strip() for ln in block if ln.strip() and not ln.strip().startswith("#")])
    # Filter
    filtered: list[str] = []
    for it in items:
        t = _strip_md_formatting(it)
        tl = t.lower()
        if not t:
            continue
        if tl in UNWANTED_OUTCOME_LINES:
            continue
        if "how will this outcome be assessed" in tl:
            continue
        if tl.startswith("at the completion of this course"):
            continue
        if tl.startswith("instructional goals"):
            continue
        if tl.startswith("outcome included in course"):
            continue
        if tl.startswith("how will this outcome be assessed"):
            continue
        if tl.startswith("required quantitative skills"):
            continue
        if tl.startswith("uaa general education"):
            continue
        if t.startswith("|"):
            continue
        filtered.append(t)
    # De-duplicate while preserving order
    seen = set()
    unique: list[str] = []
    for f in filtered:
        if f not in seen:
            seen.add(f)
            unique.append(f)
    return unique


def parse_markdown_sections(md_text: str) -> GuideSections:
    """Parse a course guide Markdown document into key sections.

    Extracts exact language for Course Description, Prerequisites,
    Instructional Goals, and Student Learning Outcomes using heading alias
    matching and light Markdown normalization.

    Returns
    - GuideSections: structured content suitable for templating.
    """
    lines = md_text.splitlines()
    # Find headings and their ranges
    sections: dict[str, tuple[int, int, int]] = {}  # title_lower -> (start_idx, end_idx, level)
    headings: list[tuple[int, str, int]] = []  # (line_idx, title_lower, level)

    for i, ln in enumerate(lines):
        m = HEADER_RE.match(ln)
        if m:
            level = len(m.group("hashes"))
            title = m.group("title").strip().lower()
            headings.append((i, title, level))

    # Determine content ranges between headings
    for idx, (line_idx, title, level) in enumerate(headings):
        # Current section goes until next heading of same or higher level
        end = len(lines)
        for j in range(idx + 1, len(headings)):
            next_idx, _, next_level = headings[j]
            if next_level <= level:
                end = next_idx
                break
        sections[title] = (line_idx + 1, end, level)

    def collect_sections_by_alias(
        aliases: list[str], exclude_substrings: list[str] | None = None
    ) -> list[list[str]]:
        matches: list[list[str]] = []
        exclude_substrings = [s.lower() for s in (exclude_substrings or [])]
        for title, (start, end, _lvl) in sections.items():
            tl = title.lower()
            if exclude_substrings and any(ex in tl for ex in exclude_substrings):
                continue
            if any(alias in tl for alias in aliases):
                content = lines[start:end]
                while content and not content[0].strip():
                    content = content[1:]
                while content and not content[-1].strip():
                    content = content[:-1]
                if content:
                    matches.append(content)
        return matches

    out = GuideSections()

    # Description and prerequisites as full text blocks
    desc_sections = collect_sections_by_alias(SECTION_ALIASES["description"])
    desc_lines = desc_sections[0] if desc_sections else []
    out.description = "\n".join(desc_lines).strip() or None

    prereq_sections = collect_sections_by_alias(SECTION_ALIASES["prerequisites"])
    prereq_lines = prereq_sections[0] if prereq_sections else []
    out.prerequisites = "\n".join(prereq_lines).strip() or None

    # Goals / outcomes: prefer bullets; merge multiple matching sections
    goals_sections = collect_sections_by_alias(SECTION_ALIASES["goals"]) or []
    if goals_sections:
        goal_items: list[str] = []
        for block in goals_sections:
            goal_items.extend(_extract_goal_items(block))
        out.goals = [g for g in goal_items if g] or None

    # Exclude general education outcomes by default for course-specific outcomes
    outcomes_sections = (
        collect_sections_by_alias(
            SECTION_ALIASES["outcomes"], exclude_substrings=["general education"]
        )
        or []
    )
    if outcomes_sections:
        outcome_items: list[str] = []
        for block in outcomes_sections:
            outcome_items.extend(_extract_outcome_items(block))
        out.outcomes = [o for o in outcome_items if o] or None

    return out


def find_guide_file(course: str) -> Path | None:
    """Locate a course guide Markdown file by course prefix.

    Accepts lower/upper/mixed file name variants.
    """
    if not GUIDES_DIR.exists():
        return None
    # Prefer markdown files with prefix
    base = course
    patterns = [
        f"{base}*.md",
        f"{base.lower()}*.md",
        f"{base.upper()}*.md",
        f"{base}*.markdown",
        f"{base.lower()}*.markdown",
        f"{base.upper()}*.markdown",
    ]
    candidates: list[Path] = []
    for pat in patterns:
        candidates.extend(GUIDES_DIR.glob(pat))
    if candidates:
        # Prefer the shortest filename (less noise) or latest mtime
        candidates.sort(key=lambda p: (len(p.name), -p.stat().st_mtime))
        return candidates[0]
    return None


def write_json(path: Path, data: dict) -> None:
    """Write JSON data to ``path`` (ensures parent directories exist)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def sync_course(course: str) -> list[str]:
    """Sync a single course's guide into JSON files used by templates.

    Behavior
    - If a standardized JSON guide exists at
      ``content/courses/<COURSE>/source/content_guide.json``, use it.
    - Otherwise, parse a Markdown guide from ``docs/reference/course-guides``.

    Returns
    - list[str]: list of relative file paths that were updated.
    """
    changes: list[str] = []
    course_dir = COURSES_DIR / course
    if not course_dir.exists():
        return changes

    # Preferred: standardized JSON source
    json_guide_path = course_dir / "source" / "content_guide.json"
    if json_guide_path.exists():
        try:
            data = json.loads(json_guide_path.read_text(encoding="utf-8"))
        except Exception:
            data = {}

        def _get_text(node: Any) -> str | None:
            if isinstance(node, str):
                return node.strip() or None
            if isinstance(node, dict):
                t = node.get("text")
                if isinstance(t, str):
                    return t.strip() or None
            return None

        desc = _get_text(data.get("description"))
        prereq = _get_text(data.get("prerequisites"))
        goals = data.get("goals") if isinstance(data.get("goals"), list) else None
        outcomes = data.get("outcomes") if isinstance(data.get("outcomes"), list) else None

        if desc:
            write_json(course_dir / "course_description.json", {"text": desc})
            changes.append("course_description.json")
        if prereq:
            write_json(course_dir / "course_prerequisites.json", {"text": prereq})
            changes.append("course_prerequisites.json")
        if goals:
            write_json(course_dir / "instructional_goals.json", {"goals": goals})
            changes.append("instructional_goals.json")
        if outcomes:
            write_json(course_dir / "student_outcomes.json", {"outcomes": outcomes})
            changes.append("student_outcomes.json")
        return changes

    # Fallback: parse Markdown guide
    guide = find_guide_file(course)
    if not guide:
        return changes
    md_text = guide.read_text(encoding="utf-8")
    sections = parse_markdown_sections(md_text)

    if sections.description:
        write_json(course_dir / "course_description.json", {"text": sections.description})
        changes.append("course_description.json")
    if sections.prerequisites:
        write_json(course_dir / "course_prerequisites.json", {"text": sections.prerequisites})
        changes.append("course_prerequisites.json")
    if sections.goals:
        write_json(course_dir / "instructional_goals.json", {"goals": sections.goals})
        changes.append("instructional_goals.json")
    if sections.outcomes:
        write_json(course_dir / "student_outcomes.json", {"outcomes": sections.outcomes})
        changes.append("student_outcomes.json")

    # Snapshot for transparency
    src_dir = course_dir / "source"
    snapshot = {
        "from_markdown": str(guide),
        "description": sections.description,
        "prerequisites": sections.prerequisites,
        "goals": sections.goals,
        "outcomes": sections.outcomes,
    }
    write_json(src_dir / "content_guide.json", snapshot)
    changes.append("source/content_guide.json")

    return changes


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync course guide Markdown into course JSON")
    parser.add_argument("--courses", nargs="*", help="Specific course codes (e.g., MATH221)")
    args = parser.parse_args()

    # Use provided courses or infer from directory structure
    courses = args.courses or [p.name for p in COURSES_DIR.iterdir() if p.is_dir()]

    for course in sorted(courses):
        changed = sync_course(course)
        if changed:
            print(f"✓ {course}: updated {', '.join(changed)}")
        else:
            print(f"– {course}: no matching guide or no updates")


if __name__ == "__main__":
    main()
