#!/usr/bin/env python3
"""
Build Blackboard content packages for course import.
Creates structured ZIP files ready for Blackboard Ultra import.
"""

import json
import os
import sys
import argparse
import zipfile
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))


class BlackboardPackageBuilder:
    """Build Blackboard import packages."""
    
    def __init__(self, output_dir: str = "build/blackboard"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def build_package(self, course_code: str) -> str:
        """Build Blackboard package for a single course."""
        print(f"Building Blackboard package for {course_code}...")
        
        # Create temporary directory for package contents
        temp_dir = self.output_dir / f"{course_code}_temp"
        temp_dir.mkdir(exist_ok=True)
        
        # Create manifest.json
        manifest = {
            "course_id": f"2025-FALL-{course_code}-901",
            "course_name": course_code,
            "created": datetime.now().isoformat(),
            "version": "1.0",
            "contents": []
        }
        
        # Add syllabus if it exists
        syllabus_html = Path(f"build/syllabi/{course_code}.html")
        if syllabus_html.exists():
            (temp_dir / "syllabus.html").write_text(syllabus_html.read_text())
            manifest["contents"].append({
                "type": "document",
                "title": "Course Syllabus",
                "file": "syllabus.html"
            })
        
        # Add schedule if it exists
        schedule_md = Path(f"build/schedules/{course_code}_schedule.md")
        if schedule_md.exists():
            (temp_dir / "schedule.md").write_text(schedule_md.read_text())
            manifest["contents"].append({
                "type": "document",
                "title": "Course Schedule",
                "file": "schedule.md"
            })
        
        # Create Start Here content
        start_here = f"""
        <h1>Welcome to {course_code} - Fall 2025</h1>
        <p>Welcome to the online section of {course_code}!</p>
        
        <h2>Getting Started</h2>
        <ul>
            <li>Review the <a href="syllabus.html">Course Syllabus</a></li>
            <li>Check the <a href="schedule.md">Course Schedule</a></li>
            <li>Complete the Week 1 Introduction Discussion</li>
            <li>Verify you can access all course materials</li>
        </ul>
        
        <h2>Contact Information</h2>
        <p>Instructor: Jeffrey Johnson<br>
        Email: jjohnson47@alaska.edu<br>
        Office Hours: By appointment</p>
        """
        
        (temp_dir / "start_here.html").write_text(start_here)
        manifest["contents"].append({
            "type": "content",
            "title": "Start Here",
            "file": "start_here.html"
        })
        
        # Write manifest
        (temp_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
        
        # Create ZIP package
        package_file = self.output_dir / f"{course_code}_package.zip"
        with zipfile.ZipFile(package_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file in temp_dir.glob("*"):
                zf.write(file, file.name)
        
        # Clean up temp directory
        for file in temp_dir.glob("*"):
            file.unlink()
        temp_dir.rmdir()
        
        return str(package_file)
    
    def build_all(self, courses=None):
        """Build packages for all courses."""
        if courses is None:
            courses = ['MATH221', 'MATH251', 'STAT253']
        
        for course in courses:
            package = self.build_package(course)
            print(f"✓ {course} package created: {package}")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description='Build Blackboard packages')
    parser.add_argument('--course', help='Build specific course')
    parser.add_argument('--output', default='build/blackboard', help='Output directory')
    parser.add_argument('--ci', action='store_true', help='CI mode')
    
    args = parser.parse_args()
    
    builder = BlackboardPackageBuilder(output_dir=args.output)
    
    if args.course:
        builder.build_package(args.course)
    else:
        builder.build_all()
    
    print(f"\nPackages built in: {args.output}/")


if __name__ == '__main__':
    main()