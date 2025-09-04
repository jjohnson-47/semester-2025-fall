#!/usr/bin/env python3
"""Add stable IDs with full provenance tracking (enhanced migration).

This enhanced version includes complete provenance tracking for all
transformations applied during the stable ID migration process.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

TERM_MAP = {"fall": "FA", "spring": "SP", "summer": "SU"}


def _term_label(term: str) -> str:
    t = term.lower()
    for k, v in TERM_MAP.items():
        if k in t:
            return v
    return "FA"


def infer_term_label(variables_file: Path) -> str:
    try:
        data = json.loads(variables_file.read_text(encoding="utf-8"))
        term = data.get("term", "Fall 2025")
        year = re.findall(r"(20\d{2})", term)
        year_s = year[0] if year else "2025"
        return f"{year_s}{_term_label(term)}"
    except Exception:
        return "2025FA"


def classify_item(label: str, is_assessment: bool) -> str:
    label_lower = label.lower()
    if is_assessment:
        if "final" in label_lower:
            return "FIN"
        if "exam" in label_lower or "midterm" in label_lower or "test" in label_lower:
            return "EXAM"
        if "quiz" in label_lower:
            return "QUIZ"
        return "EXAM"  # default assessment
    else:
        if "discussion" in label_lower or "bb" in label_lower or "blackboard" in label_lower:
            return "DISC"
        return "HW"


def generate_stable_id(prefix: str, course: str, type_code: str, seq: int) -> str:
    return f"{prefix}-{course}-{type_code}-{seq:02d}"


def create_stable_course_id(course: str, term: str, year: int) -> str:
    """Generate stable course instance ID."""
    import hashlib

    id_string = f"{course.lower()}-{term.lower()}-{year}"
    hash_suffix = hashlib.sha256(id_string.encode()).hexdigest()[:8]
    return f"{course.lower()}-{term.lower()}-{year}-{hash_suffix}"


def migrate_schedule_with_provenance(
    course: str, schedule: dict[str, Any], prefix: str
) -> dict[str, Any]:
    """Add stable IDs to assignments and assessments with full provenance tracking."""
    migration_timestamp = datetime.now(UTC).isoformat()

    out = json.loads(json.dumps(schedule))  # deep copy
    seq_map: dict[str, int] = {"HW": 0, "DISC": 0, "QUIZ": 0, "EXAM": 0, "FIN": 0}

    def _next(code: str) -> int:
        seq_map[code] += 1
        return seq_map[code]

    # Add metadata header with provenance
    stable_course_id = create_stable_course_id(course, "Fall", 2025)

    out["_meta"] = {
        "schemaVersion": "1.1.0",
        "stable_id": stable_course_id,
        "lastModified": migration_timestamp,
        "generator": "add_stable_ids_with_provenance",
        "checksum": None,  # Will be calculated after migration
        "provenance": [
            {
                "rule": "stable_id_migration_v2",
                "timestamp": migration_timestamp,
                "description": f"Enhanced stable ID migration for {course} with full provenance tracking",
                "transformation_count": 0,  # Will be updated
            }
        ],
    }

    transformation_count = 0

    for week_idx, wk in enumerate(out.get("weeks", []), 1):
        # Migrate assignments
        items: list[str] = wk.get("assignments", [])
        new_items: list[dict[str, Any]] = []
        for item_idx, label in enumerate(items):
            code = classify_item(label, is_assessment=False)
            sid = generate_stable_id(prefix, course, code, _next(code))

            new_items.append(
                {
                    "id": sid,
                    "title": label,
                    "_provenance": {
                        "source": "original",
                        "original_value": label,
                        "transformation": "string_to_object_with_stable_id",
                        "timestamp": migration_timestamp,
                        "rule": "stable_id_assignment_migration",
                        "week": week_idx,
                        "position": item_idx + 1,
                        "classification": code,
                        "confidence": 1.0,
                    },
                }
            )
            transformation_count += 1

        if new_items:
            wk["assignments"] = new_items

        # Migrate assessments
        tests: list[str] = wk.get("assessments", [])
        new_tests: list[dict[str, Any]] = []
        for item_idx, label in enumerate(tests):
            code = classify_item(label, is_assessment=True)
            sid = generate_stable_id(prefix, course, code, _next(code))

            new_tests.append(
                {
                    "id": sid,
                    "title": label,
                    "_provenance": {
                        "source": "original",
                        "original_value": label,
                        "transformation": "string_to_object_with_stable_id",
                        "timestamp": migration_timestamp,
                        "rule": "stable_id_assessment_migration",
                        "week": week_idx,
                        "position": item_idx + 1,
                        "classification": code,
                        "confidence": 1.0,
                    },
                }
            )
            transformation_count += 1

        if new_tests:
            wk["assessments"] = new_tests

    # Migrate finals
    if "finals" in out:
        finals = out["finals"]
        finals_tests: list[str] = finals.get("assessments", [])
        out_tests: list[dict[str, Any]] = []
        for item_idx, label in enumerate(finals_tests):
            sid = generate_stable_id(prefix, course, "FIN", _next("FIN"))

            out_tests.append(
                {
                    "id": sid,
                    "title": label,
                    "_provenance": {
                        "source": "original",
                        "original_value": label,
                        "transformation": "string_to_object_with_stable_id",
                        "timestamp": migration_timestamp,
                        "rule": "stable_id_finals_migration",
                        "week": "finals",
                        "position": item_idx + 1,
                        "classification": "FIN",
                        "confidence": 1.0,
                    },
                }
            )
            transformation_count += 1

        if out_tests:
            finals["assessments"] = out_tests

    # Update transformation count
    out["_meta"]["provenance"][0]["transformation_count"] = transformation_count

    # Add summary provenance
    out["_meta"]["provenance"].append(
        {
            "rule": "migration_summary",
            "timestamp": migration_timestamp,
            "description": f"Successfully migrated {transformation_count} items to stable ID format",
            "statistics": {
                "total_items": transformation_count,
                "assignments": sum(len(wk.get("assignments", [])) for wk in out.get("weeks", [])),
                "assessments": sum(len(wk.get("assessments", [])) for wk in out.get("weeks", [])),
                "finals": len(out.get("finals", {}).get("assessments", [])),
                "sequence_counters": dict(seq_map),
            },
        }
    )

    # Calculate checksum of content (excluding _meta)
    import hashlib

    content_for_checksum = {k: v for k, v in out.items() if k != "_meta"}
    content_json = json.dumps(content_for_checksum, sort_keys=True)
    checksum = hashlib.sha256(content_json.encode()).hexdigest()
    out["_meta"]["checksum"] = checksum

    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Add stable IDs with provenance tracking")
    ap.add_argument("--course", required=True, help="Course code, e.g., MATH221")
    ap.add_argument("--in", dest="in_path", required=True, help="Input schedule.json")
    ap.add_argument("--out", required=True, help="Output path for enhanced schedule")
    ap.add_argument("--vars", default="variables/semester.json", help="Variables file")
    args = ap.parse_args()

    sched = json.loads(Path(args.in_path).read_text(encoding="utf-8"))
    prefix = infer_term_label(Path(args.vars))
    migrated = migrate_schedule_with_provenance(args.course, sched, prefix)

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(migrated, indent=2), encoding="utf-8")

    # Print summary
    meta = migrated["_meta"]
    stats = meta["provenance"][1]["statistics"]
    print(f"✓ Enhanced migration complete for {args.course}")
    print(f"  Stable ID: {meta['stable_id']}")
    print(f"  Items migrated: {stats['total_items']}")
    print(f"  Checksum: {meta['checksum'][:16]}...")


if __name__ == "__main__":
    main()
