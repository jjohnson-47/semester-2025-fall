#!/usr/bin/env python3
"""Documentation consistency check.

Validates that:
- Relative Markdown links in README.md and docs/ resolve to existing files.
- ADR numbering under docs/adr/ is contiguous starting at 0001.
- Required key docs exist (architecture overview, diagram).

Exits nonzero on problems and prints a report.
"""

from __future__ import annotations

import re
import sys
from collections.abc import Iterable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def find_md_files() -> list[Path]:
    files: list[Path] = [ROOT / "README.md"]
    files += list((ROOT / "docs").rglob("*.md"))
    return [p for p in files if p.exists()]


def extract_links(md: str) -> Iterable[str]:
    # markdown links [text](target)
    for m in re.finditer(r"\[[^\]]*\]\(([^)]+)\)", md):
        yield m.group(1)


def is_relative_link(target: str) -> bool:
    return not target.startswith(("http://", "https://", "mailto:", "#"))


def check_links(files: list[Path]) -> list[tuple[Path, str]]:
    broken: list[tuple[Path, str]] = []
    for f in files:
        md = f.read_text(encoding="utf-8", errors="ignore")
        for link in extract_links(md):
            if not is_relative_link(link):
                continue
            # trim anchors in relative links
            path_part = link.split("#", 1)[0]
            if not path_part:
                continue
            target = (f.parent / path_part).resolve()
            if not target.exists():
                broken.append((f.relative_to(ROOT), link))
    return broken


def check_adr_contiguous() -> list[str]:
    problems: list[str] = []
    adr_dir = ROOT / "docs" / "adr"
    if not adr_dir.exists():
        return problems
    nums: list[int] = []
    for p in adr_dir.glob("*.md"):
        stem = p.stem
        # e.g., 0001-something
        m = re.match(r"(\d{4})-", stem)
        if m:
            nums.append(int(m.group(1)))
    if not nums:
        return problems
    nums.sort()
    expected = list(range(nums[0], nums[0] + len(nums)))
    if nums != expected:
        problems.append(f"ADR numbering not contiguous: {nums}; expected {expected}")
    if nums and nums[0] != 1:
        problems.append("ADR numbering should start at 0001")
    return problems


def check_required_docs() -> list[str]:
    required = [
        ROOT / "docs" / "REPOSITORY_ARCHITECTURE_OVERVIEW.md",
        ROOT / "docs" / "architecture-diagram.mmd",
    ]
    missing = [str(p.relative_to(ROOT)) for p in required if not p.exists()]
    return missing


def main() -> None:
    files = find_md_files()
    broken = check_links(files)
    adr_issues = check_adr_contiguous()
    missing = check_required_docs()

    ok = True
    if broken:
        ok = False
        print("Broken relative links:")
        for f, link in broken:
            print(f"  - {f}: {link}")

    if adr_issues:
        ok = False
        print("ADR issues:")
        for msg in adr_issues:
            print(f"  - {msg}")

    if missing:
        ok = False
        print("Missing required docs:")
        for p in missing:
            print(f"  - {p}")

    if not ok:
        sys.exit(1)
    print("Documentation consistency check passed.")


if __name__ == "__main__":
    main()
