#!/usr/bin/env python3
"""CSS asset handler for v2 architecture.

Manages CSS assets during build process, ensuring proper integration
with templates and maintaining course-specific styling paradigm.
"""

import logging
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)


class CSSHandler:
    """Manages CSS assets for course builds."""

    def __init__(self, assets_dir: Path = Path("assets/css"), build_dir: Path = Path("build")):
        """Initialize CSS handler.

        Args:
            assets_dir: Source directory for CSS assets
            build_dir: Build output directory
        """
        self.assets_dir = Path(assets_dir)
        self.build_dir = Path(build_dir)
        self.css_build_dir = self.build_dir / "assets" / "css"

    def setup_css_directory(self) -> None:
        """Create CSS directory structure in build."""
        self.css_build_dir.mkdir(parents=True, exist_ok=True)
        courses_dir = self.css_build_dir / "courses"
        courses_dir.mkdir(exist_ok=True)
        logger.info(f"CSS directories created at {self.css_build_dir}")

    def copy_base_styles(self) -> None:
        """Copy base course.css to build directory."""
        source = self.assets_dir / "course.css"
        if source.exists():
            dest = self.css_build_dir / "course.css"
            shutil.copy2(source, dest)
            logger.info(f"Copied base styles: {source} → {dest}")
        else:
            logger.warning(f"Base styles not found: {source}")

    def copy_course_styles(self, course_codes: list[str] | None = None) -> None:
        """Copy course-specific CSS files to build.

        Args:
            course_codes: List of course codes to copy CSS for.
                         If None, copies all found course CSS files.
        """
        courses_dir = self.assets_dir / "courses"
        if not courses_dir.exists():
            logger.warning(f"Course styles directory not found: {courses_dir}")
            return

        if course_codes is None:
            # Copy all CSS files in courses directory
            css_files = courses_dir.glob("*.css")
        else:
            # Copy only specified course CSS files
            css_files = [courses_dir / f"{code}.css" for code in course_codes]
            css_files = [f for f in css_files if f.exists()]

        for css_file in css_files:
            if css_file.exists():
                dest = self.css_build_dir / "courses" / css_file.name
                shutil.copy2(css_file, dest)
                logger.info(f"Copied course styles: {css_file.name}")

    def copy_all_assets(self, course_codes: list[str] | None = None) -> None:
        """Copy all CSS assets to build directory.

        Args:
            course_codes: Optional list of specific courses to copy CSS for
        """
        self.setup_css_directory()
        self.copy_base_styles()
        self.copy_course_styles(course_codes)

    def get_css_paths_for_template(self, course_code: str, relative_to_root: bool = True) -> dict:
        """Get CSS file paths for template rendering.

        Args:
            course_code: Course code (e.g., MATH221)
            relative_to_root: If True, paths are relative to site root
                            If False, paths are relative to current file

        Returns:
            Dictionary with 'base_css' and 'course_css' paths
        """
        if relative_to_root:
            base_path = "/assets/css/course.css"
            course_path = f"/assets/css/courses/{course_code}.css"
        else:
            base_path = "../assets/css/course.css"
            course_path = f"../assets/css/courses/{course_code}.css"

        return {"base_css": base_path, "course_css": course_path}

    def inject_inline_styles(self, course_code: str) -> str:
        """Load CSS content for inline injection if needed.

        Args:
            course_code: Course code

        Returns:
            Combined CSS content as string
        """
        css_content = []

        # Load base styles
        base_file = self.assets_dir / "course.css"
        if base_file.exists():
            css_content.append(f"/* Base Course Styles */\n{base_file.read_text()}")

        # Load course-specific styles
        course_file = self.assets_dir / "courses" / f"{course_code}.css"
        if course_file.exists():
            css_content.append(f"\n/* {course_code} Specific Styles */\n{course_file.read_text()}")

        return "\n".join(css_content) if css_content else ""
