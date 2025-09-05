#!/usr/bin/env python3
"""Public site builder for Cloudflare Pages.

Generates student-facing pages into ``site/`` with stable URLs and
embed variants. Reuses existing data loaders to preserve single
source of truth for course content and schedules.

Key responsibilities
- Render full and embed variants for syllabus pages (Phase 1)
- Generate site/manifest.json with friendly URLs and metadata
- Copy environment-specific Cloudflare headers and redirects
- Copy only necessary assets for each course

Note: This pipeline is separate from the internal ``build/`` outputs
and should not modify or depend on those HTML artifacts.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Reuse existing builders for data/context
from scripts.build_schedules import ScheduleBuilder  # noqa: E402
from scripts.build_syllabi import SyllabusBuilder  # noqa: E402
from scripts.utils.jinja_env import create_jinja_env  # noqa: E402


@dataclass
class SiteConfig:
    out_dir: Path
    env: str
    term: str
    courses: list[str]


def iso_now() -> str:
    return datetime.now(tz=UTC).isoformat(timespec="seconds")


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def copy_if_exists(src: Path, dst: Path) -> None:
    if src.exists():
        ensure_dir(dst.parent)
        shutil.copy2(src, dst)


def convert_to_embed_version(html_content: str, _course_code: str) -> str:
    """Convert full syllabus HTML to embed-friendly version."""
    # CSS paths are already absolute, no conversion needed

    # Add iframe-specific styles for better embedding
    iframe_styles = """
    <style>
        /* Iframe embedding optimizations */
        body {
            margin: 0;
            padding: 1rem;
            font-size: 0.95rem;
            line-height: 1.4;
        }
        .syllabus-container {
            box-shadow: none;
            border-radius: 0;
            padding: 0;
        }
        /* Make tables responsive in iframe */
        table {
            font-size: 0.9rem;
        }
        /* Ensure links work in iframe */
        a {
            target: '_blank';
        }
    </style>
    """

    # Insert iframe styles before closing head tag
    if "</head>" in html_content:
        html_content = html_content.replace("</head>", iframe_styles + "\n</head>")

    return html_content


def copy_js_assets(out_assets: Path) -> None:
    """Copy JavaScript assets to the site assets directory."""
    src_js_dir = PROJECT_ROOT / "assets" / "js"
    dst_js_dir = out_assets / "js"

    if src_js_dir.exists():
        ensure_dir(dst_js_dir)
        for js_file in src_js_dir.glob("*.js"):
            copy_if_exists(js_file, dst_js_dir / js_file.name)


def copy_course_assets(course_code: str, out_assets: Path) -> None:
    """Copy only the CSS files needed for this course.

    Tries the layered CSS under ``assets/`` first. Falls back to any
    ``build/css`` layout if present. Copies nothing if sources are missing.
    """
    # Preferred assets layout
    src_course_css = PROJECT_ROOT / "assets" / "css" / "course.css"
    src_course_specific_css = PROJECT_ROOT / "assets" / "css" / "courses" / f"{course_code}.css"

    # Fallback legacy layout under build/
    legacy_course_css = PROJECT_ROOT / "build" / "css" / "course.css"
    legacy_course_specific_css = PROJECT_ROOT / "build" / "css" / "courses" / f"{course_code}.css"

    dst_course_css = out_assets / "css" / "course.css"
    dst_course_specific_css = out_assets / "css" / "courses" / f"{course_code}.css"

    # Copy preferred assets if available; otherwise copy legacy if present
    if src_course_css.exists():
        copy_if_exists(src_course_css, dst_course_css)
    else:
        copy_if_exists(legacy_course_css, dst_course_css)

    if src_course_specific_css.exists():
        copy_if_exists(src_course_specific_css, dst_course_specific_css)
    else:
        copy_if_exists(legacy_course_specific_css, dst_course_specific_css)


def has_custom_due_dates(course_code: str) -> bool:
    return (PROJECT_ROOT / "content" / "courses" / course_code / "due_dates.json").exists()


def build_syllabus_pages(
    course_code: str,
    _sb: SyllabusBuilder,
    _schedule_builder: ScheduleBuilder,
    env: str,  # noqa: ARG001
    term: str,
    out_dir: Path,
    _jinja_templates: Path,
) -> dict[str, str]:
    """Copy and adapt high-quality syllabus pages from build/ directory.

    Returns a mapping of doc -> variant URLs (relative paths for manifest).
    """
    # Use existing high-quality syllabi from build/ directory
    build_dir = PROJECT_ROOT / "build" / "syllabi"
    syllabus_html_path = build_dir / f"{course_code}.html"
    # syllabus_with_calendar_path would be: build_dir / f"{course_code}_with_calendar.html"

    # Output directories
    base = out_dir / "courses" / course_code / term / "syllabus"
    base_embed = base / "embed"
    ensure_dir(base)
    ensure_dir(base_embed)

    if not syllabus_html_path.exists():
        print(f"Warning: {syllabus_html_path} not found. Run 'make syllabi' first.")
        # Create placeholder
        placeholder_html = f"""<!doctype html>
<html><head><title>{course_code} Syllabus</title></head>
<body><p>Syllabus not yet generated. Run <code>make syllabi</code> first.</p></body></html>"""
        (base / "index.html").write_text(placeholder_html, encoding="utf-8")
        (base_embed / "index.html").write_text(placeholder_html, encoding="utf-8")
    else:
        # Read the high-quality syllabus HTML
        full_html = syllabus_html_path.read_text(encoding="utf-8")

        # Create embed version by making it iframe-friendly
        embed_html = convert_to_embed_version(full_html, course_code)

        # Write the full and embed versions
        (base / "index.html").write_text(full_html, encoding="utf-8")
        (base_embed / "index.html").write_text(embed_html, encoding="utf-8")

    # Relative URLs for manifest
    rel_full = f"/courses/{course_code}/{term}/syllabus/"
    rel_embed = f"/courses/{course_code}/{term}/syllabus/embed/"
    return {"full": rel_full, "embed": rel_embed}


def build_schedule_pages(
    course_code: str,
    _sb: SyllabusBuilder,
    _schedule_builder: ScheduleBuilder,
    env: str,  # noqa: ARG001
    term: str,
    out_dir: Path,
    _jinja_templates: Path,
) -> dict[str, str]:
    """Copy and adapt high-quality schedule pages from build/ directory.

    Returns a mapping of doc -> variant URLs (relative paths for manifest).
    """
    # Use existing high-quality schedules from build/ directory
    build_dir = PROJECT_ROOT / "build" / "schedules"
    schedule_html_path = build_dir / f"{course_code}_schedule.html"

    # Output directories
    base = out_dir / "courses" / course_code / term / "schedule"
    base_embed = base / "embed"
    ensure_dir(base)
    ensure_dir(base_embed)

    if not schedule_html_path.exists():
        print(f"Warning: {schedule_html_path} not found. Run 'make schedules' first.")
        # Create placeholder
        placeholder_html = f"""<!doctype html>
<html><head><title>{course_code} Schedule</title></head>
<body><p>Schedule not yet generated. Run <code>make schedules</code> first.</p></body></html>"""
        (base / "index.html").write_text(placeholder_html, encoding="utf-8")
        (base_embed / "index.html").write_text(placeholder_html, encoding="utf-8")
    else:
        # Read the high-quality schedule HTML
        full_html = schedule_html_path.read_text(encoding="utf-8")

        # Create embed version by making it iframe-friendly
        embed_html = convert_to_embed_version(full_html, course_code)

        # Write the full and embed versions
        (base / "index.html").write_text(full_html, encoding="utf-8")
        (base_embed / "index.html").write_text(embed_html, encoding="utf-8")

    # Relative URLs for manifest
    rel_full = f"/courses/{course_code}/{term}/schedule/"
    rel_embed = f"/courses/{course_code}/{term}/schedule/embed/"
    return {"full": rel_full, "embed": rel_embed}


def write_manifest(
    out_dir: Path,
    term: str,
    courses: list[str],
    results: dict[str, dict[str, dict[str, str]]],
) -> None:
    """Write site/manifest.json following the suggested structure."""
    now = iso_now()
    courses_payload: dict[str, Any] = {}
    # Ensure all courses are present even if no docs are included
    for course in courses:
        docs = results.get(course, {})
        entry: dict[str, Any] = {
            "last_updated": now,
            "has_custom_dates": has_custom_due_dates(course),
        }
        if "syllabus" in docs:
            entry["syllabus"] = docs["syllabus"]
        if "schedule" in docs:
            entry["schedule"] = docs["schedule"]
        courses_payload[course] = entry

    manifest = {
        "generated": now,
        "term": term,
        "courses": courses_payload,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def create_default_index(courses: list[str], term: str) -> str:  # noqa: ARG001
    """Create default index.html content for the landing page."""
    course_divs = "\n        ".join(f'<div class="course">{course}</div>' for course in courses)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Course Materials - Fall 2025</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            max-width: 600px;
            margin: 100px auto;
            padding: 20px;
            text-align: center;
            color: #333;
        }}
        h1 {{
            color: #0051c3;
            font-size: 2.5em;
            margin-bottom: 0.5em;
        }}
        p {{
            font-size: 1.2em;
            line-height: 1.6;
            color: #666;
        }}
        .status {{
            background: #f0f8ff;
            padding: 15px;
            border-radius: 8px;
            margin: 30px 0;
        }}
        .courses {{
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-top: 30px;
        }}
        .course {{
            padding: 10px 20px;
            background: #e8f4f8;
            border-radius: 5px;
            font-weight: 500;
        }}
        code {{
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: "Courier New", monospace;
        }}
    </style>
</head>
<body>
    <h1>Course Materials</h1>
    <p>Fall 2025 Semester</p>

    <div class="status">
        <p><strong>✅ Course Materials Available</strong></p>
        <p>Select a course from the navigation above to access syllabi and schedules.</p>
    </div>

    <div class="courses">
        {course_divs}
    </div>

    <p style="margin-top: 50px; font-size: 0.9em; color: #999;">
        API Status: <code><a href="/manifest.json" style="color: inherit;">manifest.json</a></code> available
    </p>
</body>
</html>"""


def copy_cf_headers_redirects(out_dir: Path, env: str) -> None:
    """Copy Cloudflare headers and redirects to the site root if present."""
    cf_dir = PROJECT_ROOT / "cloudflare"
    headers_file = cf_dir / f"_headers.{env}"
    if headers_file.exists():
        shutil.copy2(headers_file, out_dir / "_headers")
    redirects = cf_dir / "_redirects"
    if redirects.exists():
        shutil.copy2(redirects, out_dir / "_redirects")
    functions_dir = cf_dir / "functions"
    if functions_dir.exists():
        shutil.copytree(functions_dir, out_dir / "functions", dirs_exist_ok=True)


def build_site(cfg: SiteConfig, include_docs: list[str], exclude_docs: list[str]) -> None:
    ensure_dir(cfg.out_dir)

    # Site templates root
    site_templates = PROJECT_ROOT / "templates" / "site"

    # Create index.html from template
    index_path = cfg.out_dir / "index.html"

    # Check if index template exists
    index_template_path = site_templates / "index.html.j2"
    if index_template_path.exists():
        # Use template for index page
        env_site = create_jinja_env(str(site_templates))
        index_template = env_site.get_template("index.html.j2")
        index_content = index_template.render(courses=cfg.courses, term=cfg.term)
    else:
        # Fall back to construction page if no template
        index_content = create_default_index(cfg.courses, cfg.term)

    index_path.write_text(index_content)

    # Prepare shared builders
    sb = SyllabusBuilder(template_dir="templates", output_dir="build/syllabi")
    schedule_builder = ScheduleBuilder(output_dir="build/schedules")

    results: dict[str, dict[str, dict[str, str]]] = {}

    # Assets root for site
    out_assets = cfg.out_dir / "assets"
    ensure_dir(out_assets)
    # Copy JavaScript assets (needed for iframe generator)
    copy_js_assets(out_assets)

    # Determine doc filters
    allowlist = {d.strip().lower() for d in include_docs if d}
    denylist = {d.strip().lower() for d in exclude_docs if d}

    for course in cfg.courses:
        # Copy just-needed assets (safe if missing)
        copy_course_assets(course, out_assets)

        course_docs: dict[str, dict[str, str]] = {}

        # Render syllabus pages (Phase 1) if allowed
        should_build_syllabus = (allowlist and "syllabus" in allowlist) or (
            not allowlist and "syllabus" not in denylist
        )
        if should_build_syllabus:
            syllabus_urls = build_syllabus_pages(
                course,
                sb,
                schedule_builder,
                cfg.env,
                cfg.term,
                cfg.out_dir,
                site_templates,
            )
            course_docs["syllabus"] = syllabus_urls

        # Render schedule pages if allowed
        should_build_schedule = (allowlist and "schedule" in allowlist) or (
            not allowlist and "schedule" not in denylist
        )
        if should_build_schedule:
            schedule_urls = build_schedule_pages(
                course,
                sb,
                schedule_builder,
                cfg.env,
                cfg.term,
                cfg.out_dir,
                site_templates,
            )
            course_docs["schedule"] = schedule_urls

        if course_docs:
            results[course] = course_docs

    # Create iframe code generator if requested
    generator_dir = cfg.out_dir / "embed" / "generator"
    ensure_dir(generator_dir)
    env_site = create_jinja_env(str(site_templates))
    generator_template = env_site.get_template("generator.html.j2")
    generator_html = generator_template.render(courses=cfg.courses, term=cfg.term)
    (generator_dir / "index.html").write_text(generator_html, encoding="utf-8")

    # Write manifest and copy CF config
    write_manifest(cfg.out_dir, cfg.term, cfg.courses, results)
    copy_cf_headers_redirects(cfg.out_dir, cfg.env)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build public site for Cloudflare Pages")
    parser.add_argument("--out", default="site", help="Output directory for site")
    parser.add_argument(
        "--env", default=os.getenv("ENV", "preview"), help="Environment: preview|prod"
    )
    parser.add_argument("--term", default="fall-2025", help="Academic term label for URLs")
    parser.add_argument(
        "--courses",
        nargs="*",
        default=["MATH221", "MATH251", "STAT253"],
        help="Courses to include",
    )
    parser.add_argument(
        "--include-docs",
        nargs="*",
        default=[],
        help="Only include these doc types (e.g., syllabus schedule). Overrides excludes.",
    )
    parser.add_argument(
        "--exclude-docs",
        nargs="*",
        default=["syllabus", "schedule"],
        help="Exclude these doc types (default excludes syllabus and schedule).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg = SiteConfig(
        out_dir=Path(args.out), env=str(args.env), term=str(args.term), courses=list(args.courses)
    )
    build_site(cfg, include_docs=args.include_docs, exclude_docs=args.exclude_docs)
    print(f"✓ Site built at {cfg.out_dir}")


if __name__ == "__main__":
    main()
