#!/usr/bin/env python3
"""Unified build pipeline (enhanced, V2-integrated).

Stages: validate → normalize → project → generate → package → report
- Verbose and dry-run support
- Per-stage execution option
- Stage results with artifacts and durations
- Build manifests and markdown/JSON reports
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.services.course_service import CourseService
from scripts.services.validation import ValidationGateway


@dataclass
class StageResult:
    stage: str
    status: str = "success"  # success | failed | skipped
    duration: float = 0.0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class BuildPipeline:
    """Staged build pipeline wired to V2 services/builders."""

    def __init__(
        self,
        courses: Iterable[str],
        *,
        build_dir: str = "build",
        verbose: bool = False,
        dry_run: bool = False,
    ) -> None:
        self.courses = list(courses)
        self.verbose = verbose
        self.dry_run = dry_run
        self.root = Path(build_dir)
        self.start = time.time()
        self.results: list[StageResult] = []
        # Back-compat: advertise stage order for tests expecting a `.stages` list
        self.stages: list[tuple[str, object]] = [
            ("validate", None),
            ("normalize", None),
            ("project", None),
            ("generate", None),
            ("package", None),
            ("report", None),
        ]

        # Directories
        self.dirs = {
            "normalized": self.root / "normalized",
            "projection": self.root / "projection",
            "v2": self.root / "v2",
            "manifests": self.root / "manifests",
            "reports": self.root / "reports",
            "package": self.root / "package",
        }
        if not self.dry_run:
            for p in self.dirs.values():
                p.mkdir(parents=True, exist_ok=True)

    # ---- utils ----
    def _log(self, stage: str, msg: str) -> None:
        if self.verbose:
            ts = time.strftime("%H:%M:%S")
            print(f"[{ts}] [{stage:9s}] {msg}")

    # ---- pipeline stages ----
    def validate(self) -> StageResult:
        st = time.time()
        res = StageResult(stage="validate")
        vg = ValidationGateway()
        for course in self.courses:
            self._log("validate", f"checking {course}")
            out = vg.validate_for_build(course)
            if not out.ok:
                res.status = "failed"
                res.errors.append(f"{course}: {'; '.join(out.messages)}")
        res.duration = time.time() - st
        self.results.append(res)
        return res

    def normalize(self) -> StageResult:
        st = time.time()
        res = StageResult(stage="normalize")
        for course in self.courses:
            in_path = Path(f"content/courses/{course}/schedule.json")
            if not in_path.exists():
                res.warnings.append(f"{course}: no schedule.json")
                continue
            try:
                from scripts.migrations.add_stable_ids import infer_term_label, migrate_schedule

                prefix = infer_term_label(Path("variables/semester.json"))
                sched = json.loads(in_path.read_text(encoding="utf-8"))
                migrated = migrate_schedule(course, sched, prefix)
                out = self.dirs["normalized"] / course / "schedule.v1_1_0.json"
                if not self.dry_run:
                    out.parent.mkdir(parents=True, exist_ok=True)
                    out.write_text(json.dumps(migrated, indent=2), encoding="utf-8")
                res.artifacts.append(str(out))
            except Exception as e:  # keep going; report at end
                res.warnings.append(f"{course}: normalize skipped ({e})")
        res.duration = time.time() - st
        self.results.append(res)
        return res

    def project(self) -> StageResult:
        st = time.time()
        res = StageResult(stage="project")
        svc = CourseService(content_dir=Path("content"))
        for course in self.courses:
            try:
                projection = svc.get_projection(course, "schedule")
                if projection:
                    out = self.dirs["projection"] / course / "schedule_projection.json"
                    if not self.dry_run:
                        out.parent.mkdir(parents=True, exist_ok=True)
                        out.write_text(
                            json.dumps(projection.to_dict(), indent=2, default=str),
                            encoding="utf-8",
                        )
                    res.artifacts.append(str(out))
            except Exception as e:
                res.errors.append(f"{course}: projection failed ({e})")
                res.status = "failed"
        res.duration = time.time() - st
        self.results.append(res)
        return res

    def generate(self) -> StageResult:
        st = time.time()
        res = StageResult(stage="generate")
        if os.getenv("BUILD_MODE", "v2").lower() != "v2":
            res.warnings.append("BUILD_MODE != v2; generation skipped")
            res.status = "skipped"
            res.duration = time.time() - st
            self.results.append(res)
            return res
        try:
            from scripts.build_schedules import ScheduleBuilder
            from scripts.build_syllabi import SyllabusBuilder

            v2_out = self.dirs["v2"]
            if not self.dry_run:
                v2_out.mkdir(parents=True, exist_ok=True)
            sched_builder = ScheduleBuilder(output_dir=str(v2_out / "schedules"))
            syllabus_builder = SyllabusBuilder(output_dir=str(v2_out / "syllabi"))
            for course in self.courses:
                self._log("generate", f"v2 HTML for {course}")
                try:
                    sched_builder.build_schedule(course)
                    syllabus_builder.build_syllabus(course)
                    res.artifacts.extend(
                        [
                            str(v2_out / "schedules" / f"{course}_schedule.html"),
                            str(v2_out / "syllabi" / f"{course}.html"),
                        ]
                    )
                except Exception as e:
                    res.warnings.append(f"{course}: generation issue ({e})")
        except Exception as e:
            res.status = "failed"
            res.errors.append(f"builders unavailable: {e}")
        res.duration = time.time() - st
        self.results.append(res)
        return res

    def package(self) -> StageResult:
        st = time.time()
        res = StageResult(stage="package")
        # Per-course manifests (compat)
        for course in self.courses:
            manifest = {
                "course_id": course,
                "v2_enabled": os.getenv("BUILD_MODE", "v2").lower() == "v2",
                "paths": {
                    "normalized": str(self.dirs["normalized"] / course / "schedule.v1_1_0.json"),
                    "projection": str(
                        self.dirs["projection"] / course / "schedule_projection.json"
                    ),
                    "v2_schedule_html": str(
                        self.dirs["v2"] / "schedules" / f"{course}_schedule.html"
                    ),
                    "v2_syllabus_html": str(self.dirs["v2"] / "syllabi" / f"{course}.html"),
                },
            }
            out = self.dirs["manifests"] / f"{course}.json"
            if not self.dry_run:
                out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            res.artifacts.append(str(out))

        # Global manifest with checksums of v2 outputs
        try:
            checksums: dict[str, str] = {}
            for course in self.courses:
                for rel in [
                    self.dirs["v2"] / "schedules" / f"{course}_schedule.html",
                    self.dirs["v2"] / "syllabi" / f"{course}.html",
                ]:
                    if rel.exists():
                        h = hashlib.sha256(rel.read_bytes()).hexdigest()
                        checksums[str(rel.relative_to(self.root))] = h
            global_manifest = {
                "build_time": time.time() - self.start,
                "checksums": checksums,
                "courses": self.courses,
            }
            out = self.dirs["package"] / "manifest.json"
            if not self.dry_run:
                out.write_text(json.dumps(global_manifest, indent=2), encoding="utf-8")
            res.artifacts.append(str(out))
        except Exception as e:
            res.warnings.append(f"global manifest skipped: {e}")

        res.duration = time.time() - st
        self.results.append(res)
        return res

    def report(self) -> StageResult:
        st = time.time()
        res = StageResult(stage="report")
        # Build a JSON summary and Markdown report
        summary = {
            "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "total_duration": time.time() - self.start,
            "stages": [
                {
                    "name": r.stage,
                    "status": r.status,
                    "duration": r.duration,
                    "errors": len(r.errors),
                    "warnings": len(r.warnings),
                    "artifacts": len(r.artifacts),
                }
                for r in self.results
            ],
        }
        json_out = self.dirs["reports"] / "build_summary.json"
        md_out = self.dirs["reports"] / "build_report.md"
        if not self.dry_run:
            json_out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
            lines = [
                "# Build Report",
                "",
                f"Generated: {summary['generated']}",
                f"Duration: {summary['total_duration']:.2f}s",
                "",
                "| Stage | Status | Duration | Errors | Warnings | Artifacts |",
                "|-------|--------|----------|--------|----------|-----------|",
            ]
            # help mypy understand this is a list of dicts
            stages_list: list[dict[str, Any]] = summary["stages"]  # type: ignore[assignment]
            for s in stages_list:
                lines.append(
                    f"| {s['name']} | {s['status']} | {s['duration']:.2f}s | {s['errors']} | {s['warnings']} | {s['artifacts']} |"
                )
            md_out.write_text("\n".join(lines), encoding="utf-8")
        res.artifacts.extend([str(json_out), str(md_out)])

        # Backward-compatible per-course short reports
        for course in self.courses:
            report = self.dirs["reports"] / f"{course}.md"
            if not self.dry_run:
                content = [
                    f"# Build Report: {course}",
                    "",
                    "- Validation: see build_summary.json",
                    "- Normalized schedule: present"
                    if (self.dirs["normalized"] / course / "schedule.v1_1_0.json").exists()
                    else "- Normalized schedule: n/a",
                    "- Projection: present"
                    if (self.dirs["projection"] / course / "schedule_projection.json").exists()
                    else "- Projection: n/a",
                ]
                report.write_text("\n".join(content), encoding="utf-8")
            res.artifacts.append(str(report))

        res.duration = time.time() - st
        self.results.append(res)
        return res

    # ---- runner ----
    def run(self, force: bool = False) -> bool:  # noqa: ARG002 - back-compat signature
        # `force` kept for backward compatibility; currently unused.
        self._log("pipeline", f"courses={self.courses}")
        if self.validate().status == "failed":
            return False
        if self.normalize().status == "failed":
            return False
        if self.project().status == "failed":
            return False
        if self.generate().status == "failed":
            return False
        if self.package().status == "failed":
            return False
        self.report()
        self._log("pipeline", f"done in {time.time() - self.start:.2f}s")
        return True


def main() -> None:  # pragma: no cover - CLI convenience
    parser = argparse.ArgumentParser(description="Run unified build pipeline (enhanced)")
    parser.add_argument("--courses", nargs="+", default=["MATH221", "MATH251", "STAT253"])
    parser.add_argument("--build-dir", default="build")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--stage", choices=["validate", "normalize", "project", "generate", "package", "report"]
    )
    args = parser.parse_args()

    pipeline = BuildPipeline(
        args.courses, build_dir=args.build_dir, verbose=args.verbose, dry_run=args.dry_run
    )

    if args.stage:
        # Invoke a single stage
        stage_fn = getattr(pipeline, args.stage)
        result: StageResult = stage_fn()
        print(f"Stage {result.stage}: {result.status} ({result.duration:.2f}s)")
        if result.errors:
            print("Errors:")
            for e in result.errors:
                print(f"  - {e}")
        sys.exit(0 if result.status in ("success", "skipped") else 1)

    ok = pipeline.run()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
