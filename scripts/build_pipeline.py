#!/usr/bin/env python3
"""Unified build pipeline (incremental implementation).

Stages: validate → normalize → project → generate → package → report
This implementation performs schema validation, writes normalized
schedule copies with stable IDs (if present), creates a projection JSON
with formatted due strings, and emits a simple per-course report.
"""

from __future__ import annotations

import json
import os
import sys
from collections.abc import Callable, Iterable
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.services.course_service import CourseService
from scripts.services.validation import ValidationGateway

StageFn = Callable[[str], None]


class BuildPipeline:
    """Minimal staged pipeline with dependency hooks."""

    def __init__(self, courses: Iterable[str]):
        self.courses = list(courses)
        self.stages: list[tuple[str, StageFn]] = [
            ("validate", self.validate_stage),
            ("normalize", self.normalize_stage),
            ("project", self.project_stage),
            ("generate", self.generate_stage),
            ("package", self.package_stage),
            ("report", self.report_stage),
        ]

    def run(self, force: bool = False) -> None:
        # Mark argument as used to appease linters while preserving API
        _ = force
        for course in self.courses:
            for _name, fn in self.stages:
                fn(course)

    # ----- Stage implementations (placeholders) -----
    def validate_stage(self, course_id: str) -> None:
        vg = ValidationGateway()
        res = vg.validate_for_build(course_id)
        if not res.ok:
            raise RuntimeError(f"validation failed for {course_id}: {'; '.join(res.messages)}")

    def normalize_stage(self, course_id: str) -> None:
        # Non-destructive stable-ID copy
        in_path = Path(f"content/courses/{course_id}/schedule.json")
        if in_path.exists():
            try:
                from scripts.migrations.add_stable_ids import infer_term_label, migrate_schedule
                prefix = infer_term_label(Path("variables/semester.json"))
                sched = json.loads(in_path.read_text(encoding="utf-8"))
                migrated = migrate_schedule(course_id, sched, prefix)
                out = Path(f"build/normalized/{course_id}/schedule.v1_1_0.json")
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(json.dumps(migrated, indent=2), encoding="utf-8")
            except Exception:
                # Keep going; report will reflect availability
                pass

    def project_stage(self, course_id: str) -> None:
        # Compute schedule projection JSON using service-level logic
        svc = CourseService(content_dir=Path("content"))
        projection = svc.get_projection(course_id, "schedule")
        if projection:
            out = Path(f"build/projection/{course_id}/schedule_projection.json")
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(projection.to_dict(), indent=2, default=str), encoding="utf-8")

    def generate_stage(self, course_id: str) -> None:
        # v2: generate HTML using builders into build/v2/*
        if os.getenv("BUILD_MODE", "v2").lower() != "v2":
            import warnings
            warnings.warn(
                "Legacy mode is deprecated. Skipping v2 generation.",
                DeprecationWarning,
                stacklevel=2,
            )
            return
        try:
            from scripts.build_schedules import ScheduleBuilder
            from scripts.build_syllabi import SyllabusBuilder
            v2_out = Path("build/v2")
            v2_out.mkdir(parents=True, exist_ok=True)
            sched_builder = ScheduleBuilder(output_dir=str(v2_out / "schedules"))
            syllabus_builder = SyllabusBuilder(output_dir=str(v2_out / "syllabi"))
            sched_builder.build_schedule(course_id)
            syllabus_builder.build_syllabus(course_id)
        except Exception:
            # Non-fatal until full cutover
            pass

    def package_stage(self, course_id: str) -> None:
        # Emit a simple manifest describing generated artifacts
        manifest_dir = Path("build/manifests")
        manifest_dir.mkdir(parents=True, exist_ok=True)
        manifest_file = manifest_dir / f"{course_id}.json"
        manifest = {
            "course_id": course_id,
            "v2_enabled": os.getenv("BUILD_MODE", "v2").lower() == "v2",
            "paths": {
                "normalized": f"build/normalized/{course_id}/schedule.v1_1_0.json",
                "projection": f"build/projection/{course_id}/schedule_projection.json",
                "v2_schedule_html": f"build/v2/schedules/{course_id}_schedule.html",
                "v2_syllabus_html": f"build/v2/syllabi/{course_id}.html",
            },
        }
        manifest_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    def report_stage(self, course_id: str) -> None:
        report = Path(f"build/reports/{course_id}.md")
        report.parent.mkdir(parents=True, exist_ok=True)
        content = [
            f"# Build Report: {course_id}",
            "",
            "- Validation: OK",
            "- Normalized schedule: present" if Path(f"build/normalized/{course_id}/schedule.v1_1_0.json").exists() else "- Normalized schedule: n/a",
            "- Projection: present" if Path(f"build/projection/{course_id}/schedule_projection.json").exists() else "- Projection: n/a",
        ]
        report.write_text("\n".join(content), encoding="utf-8")


def main() -> None:  # pragma: no cover - CLI convenience
    import argparse

    parser = argparse.ArgumentParser(description="Run unified build pipeline (scaffold)")
    parser.add_argument("--courses", nargs="+", default=["MATH221", "MATH251", "STAT253"])
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    pipeline = BuildPipeline(args.courses)
    pipeline.run(force=args.force)


if __name__ == "__main__":
    main()
