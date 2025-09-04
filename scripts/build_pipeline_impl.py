#!/usr/bin/env python3
"""Compatibility wrapper for the pre-refactor pipeline implementation.

This module defers to the enhanced pipeline in `scripts/build_pipeline.py`.
It preserves the original CLI and class name so the feature branch can merge
without disrupting usage or documentation that referenced this path.
"""

from __future__ import annotations

from scripts.build_pipeline import BuildPipeline as BuildPipeline  # noqa: F401


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

  pipeline = BuildPipeline(args.courses, build_dir=args.build_dir, verbose=args.verbose, dry_run=args.dry_run)

  if args.stage:
    stage_method = getattr(pipeline, args.stage)
    result = stage_method()
    print(f"Stage {result.stage}: {result.status}")
    raise SystemExit(0 if result.status in ("success", "skipped") else 1)

  ok = pipeline.run()
  raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
  main()
"""Unified build pipeline for course content generation - Full Implementation.

Stages:
1. Validate - Check JSON schemas and data integrity
2. Normalize - Apply rules engine to create normalized data
3. Project - Generate view projections for different outputs
4. Generate - Create HTML, MD, and other formats
5. Package - Bundle for deployment
6. Report - Generate build reports and manifests
"""

import argparse
import json
import hashlib
import shutil
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class StageResult:
    """Result from a pipeline stage."""
    stage: str
    status: str  # success, failed, skipped
    duration: float
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    artifacts: List[Path] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BuildManifest:
    """Build manifest for tracking outputs."""
    build_id: str
    timestamp: str
    courses: List[str]
    stages: List[StageResult]
    total_duration: float
    output_dir: Path
    checksums: Dict[str, str] = field(default_factory=dict)


class BuildPipeline:
    """Orchestrates the build stages.
    
    Each stage is idempotent and can be run independently.
    Stages communicate via the build directory structure.
    """

    def __init__(self, 
                 build_dir: Path = Path("build"),
                 verbose: bool = False,
                 dry_run: bool = False):
        """Initialize pipeline.
        
        Args:
            build_dir: Root build directory
            verbose: Enable verbose output
            dry_run: Don't write files, just simulate
        """
        self.build_dir = Path(build_dir)
        self.verbose = verbose
        self.dry_run = dry_run
        self.results: List[StageResult] = []
        self.start_time = time.time()
        
        # Create build directories
        self.dirs = {
            "validate": self.build_dir / "validate",
            "normalize": self.build_dir / "normalize",
            "project": self.build_dir / "project",
            "generate": self.build_dir / "generate",
            "package": self.build_dir / "package",
            "reports": self.build_dir / "reports",
        }
        
        if not dry_run:
            for dir_path in self.dirs.values():
                dir_path.mkdir(parents=True, exist_ok=True)
    
    def _log(self, stage: str, message: str) -> None:
        """Log a message if verbose."""
        if self.verbose:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] [{stage:10s}] {message}")
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of a file."""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def validate(self, courses: List[str]) -> StageResult:
        """Stage 1: Validate input data.
        
        - Check JSON syntax
        - Verify required fields
        - Check referential integrity
        - Validate against schema
        """
        stage_start = time.time()
        self._log("VALIDATE", f"Validating {len(courses)} courses")
        
        result = StageResult(
            stage="validate",
            status="success",
            duration=0
        )
        
        for course in courses:
            self._log("VALIDATE", f"Checking {course}")
            course_dir = Path("content/courses") / course
            
            if not course_dir.exists():
                result.errors.append(f"Course directory not found: {course_dir}")
                result.status = "failed"
                continue
            
            # Check required JSON files
            required_files = [
                "course_meta.json",
                "schedule.json",
                "syllabus_data.json",
                "policies.json",
            ]
            
            for req_file in required_files:
                file_path = course_dir / req_file
                if not file_path.exists():
                    result.warnings.append(f"Missing {req_file} for {course}")
                    continue
                
                # Validate JSON syntax
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Write validated JSON to build dir
                    if not self.dry_run:
                        output_dir = self.dirs["validate"] / course
                        output_dir.mkdir(exist_ok=True)
                        output_file = output_dir / req_file
                        
                        with open(output_file, 'w', encoding='utf-8') as f:
                            json.dump(data, f, indent=2)
                        
                        result.artifacts.append(output_file)
                        
                except json.JSONDecodeError as e:
                    result.errors.append(f"Invalid JSON in {file_path}: {e}")
                    result.status = "failed"
        
        result.duration = time.time() - stage_start
        result.metadata["courses_validated"] = len(courses)
        result.metadata["files_validated"] = len(result.artifacts)
        
        self._log("VALIDATE", f"Completed in {result.duration:.2f}s")
        self.results.append(result)
        return result
    
    def normalize(self, courses: List[str]) -> StageResult:
        """Stage 2: Normalize with rules engine.
        
        - Apply date rules
        - Normalize field names
        - Add computed fields
        - Ensure consistency
        """
        stage_start = time.time()
        self._log("NORMALIZE", f"Normalizing {len(courses)} courses")
        
        result = StageResult(
            stage="normalize",
            status="success",
            duration=0
        )
        
        # Import rules engine components
        try:
            from rules.engine import CourseRulesEngine
            from rules.models import NormalizedCourse
            engine = CourseRulesEngine()
        except ImportError:
            # Fallback for now
            engine = None
            result.warnings.append("Rules engine not available, using passthrough")
        
        for course in courses:
            self._log("NORMALIZE", f"Processing {course}")
            
            # Load validated data
            validated_dir = self.dirs["validate"] / course
            if not validated_dir.exists():
                result.errors.append(f"No validated data for {course}")
                continue
            
            # Create normalized structure
            normalized = {
                "course_code": course,
                "normalized_at": datetime.utcnow().isoformat(),
                "schema_version": "1.1.0",
                "data": {}
            }
            
            # Load and normalize each component
            for json_file in validated_dir.glob("*.json"):
                with open(json_file, 'r') as f:
                    data = json.load(f)
                
                # Apply normalization rules
                if engine:
                    # Use real engine when available
                    pass
                else:
                    # Simple passthrough for now
                    normalized["data"][json_file.stem] = data
            
            # Write normalized data
            if not self.dry_run:
                output_file = self.dirs["normalize"] / f"{course}_normalized.json"
                with open(output_file, 'w') as f:
                    json.dump(normalized, f, indent=2)
                
                result.artifacts.append(output_file)
                result.metadata[f"{course}_fields"] = len(normalized["data"])
        
        result.duration = time.time() - stage_start
        self._log("NORMALIZE", f"Completed in {result.duration:.2f}s")
        self.results.append(result)
        return result
    
    def project(self, courses: List[str]) -> StageResult:
        """Stage 3: Create view projections.
        
        - Syllabus projection
        - Schedule projection
        - Dashboard projection
        - Blackboard projection
        """
        stage_start = time.time()
        self._log("PROJECT", f"Creating projections for {len(courses)} courses")
        
        result = StageResult(
            stage="project",
            status="success",
            duration=0
        )
        
        projections = [
            "syllabus",
            "schedule",
            "dashboard",
            "blackboard",
            "intelligence",
        ]
        
        for course in courses:
            self._log("PROJECT", f"Projecting {course}")
            
            # Load normalized data
            normalized_file = self.dirs["normalize"] / f"{course}_normalized.json"
            if not normalized_file.exists():
                result.errors.append(f"No normalized data for {course}")
                continue
            
            with open(normalized_file, 'r') as f:
                normalized = json.load(f)
            
            # Create projections
            for proj_type in projections:
                projection = self._create_projection(normalized, proj_type)
                
                if not self.dry_run:
                    output_dir = self.dirs["project"] / course
                    output_dir.mkdir(exist_ok=True)
                    output_file = output_dir / f"{proj_type}_projection.json"
                    
                    with open(output_file, 'w') as f:
                        json.dump(projection, f, indent=2)
                    
                    result.artifacts.append(output_file)
        
        result.duration = time.time() - stage_start
        result.metadata["projections_created"] = len(result.artifacts)
        self._log("PROJECT", f"Completed in {result.duration:.2f}s")
        self.results.append(result)
        return result
    
    def _create_projection(self, normalized: Dict[str, Any], 
                          proj_type: str) -> Dict[str, Any]:
        """Create a specific projection from normalized data."""
        projection = {
            "type": proj_type,
            "course_code": normalized["course_code"],
            "created_at": datetime.utcnow().isoformat(),
        }
        
        data = normalized.get("data", {})
        
        if proj_type == "syllabus":
            # Extract syllabus-specific fields
            projection["content"] = {
                "course_info": data.get("course_meta", {}),
                "policies": data.get("policies", {}),
                "evaluation": data.get("evaluation_tools", {}),
                "schedule_summary": self._summarize_schedule(data.get("schedule", {}))
            }
        elif proj_type == "schedule":
            # Extract schedule-specific fields
            projection["content"] = {
                "weeks": data.get("schedule", {}).get("weeks", []),
                "finals": data.get("schedule", {}).get("finals", {}),
                "important_dates": data.get("course_meta", {}).get("important_dates", {})
            }
        elif proj_type == "dashboard":
            # Extract dashboard-relevant fields
            projection["content"] = {
                "tasks": self._extract_tasks(data),
                "milestones": self._extract_milestones(data),
                "stats": self._calculate_stats(data)
            }
        elif proj_type == "blackboard":
            # Blackboard-specific formatting
            projection["content"] = {
                "announcements": [],
                "content_areas": self._format_for_blackboard(data),
                "gradebook_columns": self._extract_gradebook_columns(data)
            }
        elif proj_type == "intelligence":
            # AI/intelligence projection
            projection["content"] = {
                "summary": self._generate_summary(data),
                "key_dates": self._extract_key_dates(data),
                "workload_analysis": self._analyze_workload(data)
            }
        
        return projection
    
    def _summarize_schedule(self, schedule: Dict[str, Any]) -> Dict[str, Any]:
        """Create schedule summary."""
        weeks = schedule.get("weeks", [])
        return {
            "total_weeks": len(weeks),
            "topics": [w.get("topic", "") for w in weeks],
            "major_assessments": sum(1 for w in weeks if w.get("assessments"))
        }
    
    def _extract_tasks(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract tasks from course data."""
        tasks = []
        # TODO: Implement task extraction logic
        return tasks
    
    def _extract_milestones(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract milestones from course data."""
        milestones = []
        # TODO: Implement milestone extraction
        return milestones
    
    def _calculate_stats(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate course statistics."""
        return {
            "total_assignments": 0,  # TODO: Calculate
            "total_assessments": 0,  # TODO: Calculate
            "workload_hours": 0,  # TODO: Estimate
        }
    
    def _format_for_blackboard(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format content for Blackboard."""
        return {}  # TODO: Implement
    
    def _extract_gradebook_columns(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract gradebook structure."""
        return []  # TODO: Implement
    
    def _generate_summary(self, data: Dict[str, Any]) -> str:
        """Generate course summary."""
        return "Course summary pending"  # TODO: Implement
    
    def _extract_key_dates(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract key dates."""
        return []  # TODO: Implement
    
    def _analyze_workload(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze course workload."""
        return {}  # TODO: Implement
    
    def generate(self, courses: List[str]) -> StageResult:
        """Stage 4: Generate output formats.
        
        - HTML files
        - Markdown files
        - JSON exports
        """
        stage_start = time.time()
        self._log("GENERATE", f"Generating outputs for {len(courses)} courses")
        
        result = StageResult(
            stage="generate",
            status="success",
            duration=0
        )
        
        # For now, copy projections as-is
        # TODO: Implement actual generation with templates
        
        for course in courses:
            project_dir = self.dirs["project"] / course
            if not project_dir.exists():
                result.errors.append(f"No projections for {course}")
                continue
            
            if not self.dry_run:
                output_dir = self.dirs["generate"] / course
                output_dir.mkdir(exist_ok=True)
                
                for projection_file in project_dir.glob("*.json"):
                    # For now, just copy
                    # TODO: Generate HTML/MD from projections
                    shutil.copy2(projection_file, output_dir)
                    result.artifacts.append(output_dir / projection_file.name)
        
        result.duration = time.time() - stage_start
        self._log("GENERATE", f"Completed in {result.duration:.2f}s")
        self.results.append(result)
        return result
    
    def package(self, courses: List[str]) -> StageResult:
        """Stage 5: Package for deployment.
        
        - Create deployment bundle
        - Generate manifest
        - Calculate checksums
        """
        stage_start = time.time()
        self._log("PACKAGE", f"Packaging {len(courses)} courses")
        
        result = StageResult(
            stage="package",
            status="success",
            duration=0
        )
        
        # Create deployment structure
        if not self.dry_run:
            deploy_dir = self.dirs["package"] / "deploy"
            deploy_dir.mkdir(exist_ok=True)
            
            # Copy generated files
            for course in courses:
                gen_dir = self.dirs["generate"] / course
                if gen_dir.exists():
                    dest_dir = deploy_dir / course
                    if dest_dir.exists():
                        shutil.rmtree(dest_dir)
                    shutil.copytree(gen_dir, dest_dir)
                    result.artifacts.append(dest_dir)
            
            # Create manifest
            manifest = BuildManifest(
                build_id=hashlib.sha256(str(time.time()).encode()).hexdigest()[:8],
                timestamp=datetime.utcnow().isoformat(),
                courses=courses,
                stages=self.results,
                total_duration=time.time() - self.start_time,
                output_dir=deploy_dir
            )
            
            # Calculate checksums
            for artifact in deploy_dir.rglob("*"):
                if artifact.is_file():
                    rel_path = artifact.relative_to(deploy_dir)
                    manifest.checksums[str(rel_path)] = self._calculate_checksum(artifact)
            
            # Write manifest
            manifest_file = deploy_dir / "manifest.json"
            with open(manifest_file, 'w') as f:
                json.dump({
                    "build_id": manifest.build_id,
                    "timestamp": manifest.timestamp,
                    "courses": manifest.courses,
                    "total_duration": manifest.total_duration,
                    "checksums": manifest.checksums
                }, f, indent=2)
            
            result.artifacts.append(manifest_file)
        
        result.duration = time.time() - stage_start
        self._log("PACKAGE", f"Completed in {result.duration:.2f}s")
        self.results.append(result)
        return result
    
    def report(self) -> StageResult:
        """Stage 6: Generate reports.
        
        - Build summary
        - Per-course reports
        - Error report
        - Performance metrics
        """
        stage_start = time.time()
        self._log("REPORT", "Generating reports")
        
        result = StageResult(
            stage="report",
            status="success",
            duration=0
        )
        
        if not self.dry_run:
            # Generate build summary
            summary = {
                "build_time": datetime.utcnow().isoformat(),
                "total_duration": time.time() - self.start_time,
                "stages": []
            }
            
            for stage_result in self.results:
                summary["stages"].append({
                    "name": stage_result.stage,
                    "status": stage_result.status,
                    "duration": stage_result.duration,
                    "errors": len(stage_result.errors),
                    "warnings": len(stage_result.warnings),
                    "artifacts": len(stage_result.artifacts)
                })
            
            # Write summary
            summary_file = self.dirs["reports"] / "build_summary.json"
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
            
            result.artifacts.append(summary_file)
            
            # Generate markdown report
            report_md = self._generate_markdown_report(summary)
            report_file = self.dirs["reports"] / "build_report.md"
            with open(report_file, 'w') as f:
                f.write(report_md)
            
            result.artifacts.append(report_file)
        
        result.duration = time.time() - stage_start
        self._log("REPORT", f"Completed in {result.duration:.2f}s")
        self.results.append(result)
        return result
    
    def _generate_markdown_report(self, summary: Dict[str, Any]) -> str:
        """Generate markdown build report."""
        lines = [
            "# Build Report",
            "",
            f"**Generated:** {summary['build_time']}",
            f"**Duration:** {summary['total_duration']:.2f} seconds",
            "",
            "## Stage Summary",
            "",
            "| Stage | Status | Duration | Errors | Warnings | Artifacts |",
            "|-------|--------|----------|--------|----------|-----------|"
        ]
        
        for stage in summary["stages"]:
            lines.append(
                f"| {stage['name']} | {stage['status']} | "
                f"{stage['duration']:.2f}s | {stage['errors']} | "
                f"{stage['warnings']} | {stage['artifacts']} |"
            )
        
        return "\n".join(lines)
    
    def run(self, courses: List[str]) -> bool:
        """Run the complete pipeline."""
        try:
            self._log("PIPELINE", f"Starting build for {courses}")
            
            # Stage 1: Validate
            validate_result = self.validate(courses)
            if validate_result.status == "failed":
                self._log("PIPELINE", "Validation failed, stopping")
                return False
            
            # Stage 2: Normalize
            normalize_result = self.normalize(courses)
            if normalize_result.status == "failed":
                self._log("PIPELINE", "Normalization failed, stopping")
                return False
            
            # Stage 3: Project
            project_result = self.project(courses)
            if project_result.status == "failed":
                self._log("PIPELINE", "Projection failed, stopping")
                return False
            
            # Stage 4: Generate
            generate_result = self.generate(courses)
            if generate_result.status == "failed":
                self._log("PIPELINE", "Generation failed, stopping")
                return False
            
            # Stage 5: Package
            package_result = self.package(courses)
            if package_result.status == "failed":
                self._log("PIPELINE", "Packaging failed, stopping")
                return False
            
            # Stage 6: Report
            report_result = self.report()
            
            total_time = time.time() - self.start_time
            self._log("PIPELINE", f"Completed successfully in {total_time:.2f}s")
            return True
            
        except Exception as e:
            self._log("PIPELINE", f"Failed with error: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description="Unified build pipeline")
    parser.add_argument(
        "--courses",
        nargs="+",
        default=["MATH221", "MATH251", "STAT253"],
        help="Courses to build",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose output"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Simulate without writing files"
    )
    parser.add_argument(
        "--stage",
        choices=["validate", "normalize", "project", "generate", "package", "report"],
        help="Run only specified stage",
    )
    parser.add_argument(
        "--build-dir",
        default="build",
        help="Build directory (default: build)"
    )

    args = parser.parse_args()

    pipeline = BuildPipeline(
        build_dir=Path(args.build_dir),
        verbose=args.verbose,
        dry_run=args.dry_run
    )

    if args.stage:
        # Run single stage
        print(f"Running stage: {args.stage}")
        stage_method = getattr(pipeline, args.stage)
        result = stage_method(args.courses)
        print(f"Stage {args.stage}: {result.status}")
        if result.errors:
            print("Errors:")
            for error in result.errors:
                print(f"  - {error}")
        sys.exit(0 if result.status == "success" else 1)
    else:
        # Run full pipeline
        success = pipeline.run(args.courses)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
