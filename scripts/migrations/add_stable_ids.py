#!/usr/bin/env python3
"""Add stable IDs to schedule-like structures (non-destructive).

Reads a course schedule JSON and emits a normalized copy with IDs for
assignments and assessments. Original schedule is untouched.

ID format (default): {YYYY}{TERM}-{COURSE}-{TYPE}-{NN}
  TERM: FA|SP|SU
  TYPE: HW|DISC|QUIZ|EXAM|FIN
"""

from __future__ import annotations

import argparse
import json
import re
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
        return "EXAM"
    # assignments
    if "discussion" in label_lower or "blackboard" in label_lower or label_lower.startswith("bb"):
        return "DISC"
    return "HW"


def generate_stable_id(prefix: str, course: str, type_code: str, seq: int) -> str:
    return f"{prefix}-{course}-{type_code}-{seq:02d}"


def migrate_schedule(course: str, schedule: dict[str, Any], prefix: str) -> dict[str, Any]:
    out = json.loads(json.dumps(schedule))  # deep copy
    seq_map: dict[str, int] = {"HW": 0, "DISC": 0, "QUIZ": 0, "EXAM": 0, "FIN": 0}

    def _next(code: str) -> int:
        seq_map[code] += 1
        return seq_map[code]

    for wk in out.get("weeks", []):
        items: list[str] = wk.get("assignments", [])
        new_items: list[dict[str, Any]] = []
        for label in items:
            code = classify_item(label, is_assessment=False)
            sid = generate_stable_id(prefix, course, code, _next(code))
            new_items.append({"id": sid, "title": label})
        wk["assignments"] = new_items

        tests: list[str] = wk.get("assessments", [])
        new_tests: list[dict[str, Any]] = []
        for label in tests:
            code = classify_item(label, is_assessment=True)
            sid = generate_stable_id(prefix, course, code, _next(code))
            new_tests.append({"id": sid, "title": label})
        wk["assessments"] = new_tests

    if "finals" in out:
        finals = out["finals"]
        finals_tests: list[str] = finals.get("assessments", [])
        out_tests: list[dict[str, Any]] = []
        for label in finals_tests:
            sid = generate_stable_id(prefix, course, "FIN", _next("FIN"))
            out_tests.append({"id": sid, "title": label})
        finals["assessments"] = out_tests
    return out


def main() -> None:  # pragma: no cover - CLI
    ap = argparse.ArgumentParser(description="Add stable IDs to schedule (to new file)")
    ap.add_argument("--course", required=True, help="Course code, e.g., MATH221")
    ap.add_argument("--in", dest="in_path", required=True, help="Input schedule.json")
    ap.add_argument("--out", required=True, help="Output path for migrated schedule")
    ap.add_argument("--vars", default="variables/semester.json", help="Variables file to infer term")
    args = ap.parse_args()

    sched = json.loads(Path(args.in_path).read_text(encoding="utf-8"))
    prefix = infer_term_label(Path(args.vars))
    migrated = migrate_schedule(args.course, sched, prefix)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(migrated, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()

