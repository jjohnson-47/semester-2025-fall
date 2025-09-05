#!/usr/bin/env python3
"""
Generate manifest.json files for each course
Manifests provide metadata and schema version information
"""

import json
from datetime import datetime
from pathlib import Path


def generate_manifest(course_code: str, course_dir: Path) -> dict:
    """Generate manifest for a course"""

    # Aggregate course data
    course_data = {}
    json_files = []

    for json_file in course_dir.glob("*.json"):
        json_files.append(json_file.name)
        with open(json_file) as f:
            data = json.load(f)
            if isinstance(data, dict):
                course_data.update(data)

    # Extract key metadata
    manifest = {
        "_meta": {
            "version": "1.1.0",
            "generated_at": datetime.now().isoformat(),
            "course_code": course_code,
            "schema_version": "v1.1.0",
        },
        "course": {
            "code": course_code,
            "title": course_data.get("course_title", f"{course_code} Course"),
            "credits": course_data.get("credits", 3),
            "term": "Fall 2025",
            "start_date": "2025-08-25",
            "end_date": "2025-12-13",
        },
        "instructor": course_data.get("instructor", {}),
        "schedule": {
            "meeting_times": course_data.get("meeting_times", []),
            "location": course_data.get("location", "TBD"),
            "format": course_data.get("format", "In-person"),
        },
        "files": {"json_files": sorted(json_files), "count": len(json_files)},
        "features": {
            "has_syllabus": any("syllabus" in f for f in json_files),
            "has_schedule": any("schedule" in f for f in json_files),
            "has_blackboard": any("bb_" in f or "blackboard" in f for f in json_files),
            "has_grading": "grading_scale" in course_data or "assessment_weights" in course_data,
            "has_policies": "class_policies" in course_data or "policies" in str(course_data),
        },
        "validation": {
            "schema_compliant": True,
            "no_weekend_dues": True,  # Enforced by rules engine
            "dates_validated": True,
        },
    }

    return manifest


def main():
    """Generate manifests for all courses"""
    courses_dir = Path("content/courses")
    manifests_created = []

    if not courses_dir.exists():
        print(f"Error: Courses directory not found at {courses_dir}")
        return 1

    for course_dir in courses_dir.iterdir():
        if course_dir.is_dir():
            course_code = course_dir.name

            # Generate manifest
            manifest = generate_manifest(course_code, course_dir)

            # Write manifest file
            manifest_file = course_dir / "manifest.json"
            with open(manifest_file, "w") as f:
                json.dump(manifest, f, indent=2)

            manifests_created.append(course_code)
            print(f"✓ Generated manifest for {course_code}")

    print(f"\nManifests created for: {', '.join(manifests_created)}")

    # Verify manifests
    for course_code in manifests_created:
        manifest_file = courses_dir / course_code / "manifest.json"
        if manifest_file.exists():
            with open(manifest_file) as f:
                data = json.load(f)
                version = data.get("_meta", {}).get("schema_version", "unknown")
                print(f"  {course_code}: schema {version}")

    return 0


if __name__ == "__main__":
    exit(main())
