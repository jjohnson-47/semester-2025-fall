#!/usr/bin/env python3
"""Compatibility wrapper for the pre-refactor pipeline implementation.

This module defers to the enhanced pipeline in `scripts/build_pipeline.py`.
It preserves the original CLI and class name so the feature branch can merge
without disrupting usage or documentation that referenced this path.
"""

from __future__ import annotations

import warnings

from scripts.build_pipeline import BuildPipeline as BuildPipeline  # re-export

warnings.warn(
    "scripts.build_pipeline_impl is deprecated and will be removed after Fall 2025. "
    "Use scripts.build_pipeline instead.",
    DeprecationWarning,
    stacklevel=2,
)


def main() -> None:  # pragma: no cover - CLI shim
    import argparse

    parser = argparse.ArgumentParser(description="Unified build pipeline (compat)")
    parser.add_argument(
        "--courses", nargs="+", default=["MATH221", "MATH251", "STAT253"], help="Courses to build"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without writing files")
    parser.add_argument(
        "--stage",
        choices=["validate", "normalize", "project", "generate", "package", "report"],
        help="Run only specified stage",
    )
    parser.add_argument("--build-dir", default="build", help="Build directory (default: build)")

    args = parser.parse_args()

    pipeline = BuildPipeline(
        args.courses, build_dir=args.build_dir, verbose=args.verbose, dry_run=args.dry_run
    )

    if args.stage:
        stage_method = getattr(pipeline, args.stage)
        result = stage_method()
        print(f"Stage {result.stage}: {result.status}")
        raise SystemExit(0 if result.status in ("success", "skipped") else 1)

    ok = pipeline.run()
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()

