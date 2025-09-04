#!/usr/bin/env python3
"""Validate course schedules against v1.1.0 schema.

Usage:
  uv run python scripts/validate_v110.py --course MATH221
  uv run python scripts/validate_v110.py --all
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.services.validation import ValidationGateway


def iter_courses() -> Iterable[str]:
    root = Path("content/courses")
    for d in sorted(p for p in root.iterdir() if p.is_dir()):
        yield d.name


def validate_course(course: str) -> bool:
    vg = ValidationGateway()
    path = Path(f"content/courses/{course}/schedule.json")
    if not path.exists():
        print(f"- {course}: schedule.json not found (skipping)")
        return True
    data = json.loads(path.read_text(encoding="utf-8"))
    res = vg.validate_schedule_v1_1_0(data)
    if res.ok:
        print(f"✓ {course}: schedule.json valid v1.1.0-compatible")
        return True
    print(f"✗ {course}: " + "; ".join(res.messages))
    return False


def main() -> None:
    ap = argparse.ArgumentParser(description="Validate schedules against v1.1.0 schema")
    ap.add_argument("--course", help="One course code (e.g., MATH221)")
    ap.add_argument(
        "--all", action="store_true", help="Validate all courses under content/courses/"
    )
    args = ap.parse_args()

    ok = True
    if args.course:
        ok = validate_course(args.course)
    elif args.all:
        for c in iter_courses():
            ok = validate_course(c) and ok
    else:
        ap.error("Provide --course or --all")

    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
