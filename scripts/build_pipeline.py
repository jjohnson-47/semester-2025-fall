#!/usr/bin/env python3
"""Unified build pipeline (scaffold).

Stages: validate → normalize → project → generate → package → report
This initial implementation is a no-op pipeline intended for CI wiring
and parallel agent development. It does not change existing Make targets.
"""

from __future__ import annotations

from typing import Callable, Iterable


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
        _ = force
        for course in self.courses:
            for name, fn in self.stages:
                fn(course)

    # ----- Stage implementations (placeholders) -----
    def validate_stage(self, course_id: str) -> None:
        _ = course_id

    def normalize_stage(self, course_id: str) -> None:
        _ = course_id

    def project_stage(self, course_id: str) -> None:
        _ = course_id

    def generate_stage(self, course_id: str) -> None:
        _ = course_id

    def package_stage(self, course_id: str) -> None:
        _ = course_id

    def report_stage(self, course_id: str) -> None:
        _ = course_id


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

