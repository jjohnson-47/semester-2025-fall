#!/usr/bin/env python3
"""
Unit tests for scripts.services.validation.ValidationGateway.
"""

from __future__ import annotations

import json
from pathlib import Path

from scripts.services.validation import ValidationGateway


def test_validate_for_build_with_minimal_files(tmp_path: Path) -> None:
    # Create minimal course files
    course_dir = tmp_path / "content" / "courses" / "TEST101"
    course_dir.mkdir(parents=True)
    (course_dir / "schedule.json").write_text(json.dumps({"weeks": []}))
    (course_dir / "syllabus.json").write_text(json.dumps({"course_code": "TEST101"}))

    vg = ValidationGateway()
    # Patch working directory to tmp tree
    cwd = Path.cwd()
    try:
        import os

        os.chdir(tmp_path)
        res = vg.validate_for_build("TEST101")
        assert res is not None and hasattr(res, "ok")
    finally:
        os.chdir(cwd)
