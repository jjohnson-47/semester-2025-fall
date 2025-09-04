#!/usr/bin/env python3
"""Merge Cobertura coverage XMLs and emit a summary.

This script reads one or more coverage.xml files (coverage.py Cobertura
format), sums lines-covered and lines-valid, and writes a combined XML
stub and a Markdown summary. Branch stats are summed if present.

Usage:
  python scripts/ops/coverage_merge.py --inputs path1.xml path2.xml \
      --out-xml combined-coverage.xml --out-md coverage-summary.md
"""

from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Totals:
    lines_valid: int = 0
    lines_covered: int = 0
    branches_valid: int = 0
    branches_covered: int = 0

    @property
    def line_rate(self) -> float:
        return (self.lines_covered / self.lines_valid) if self.lines_valid else 0.0

    @property
    def branch_rate(self) -> float:
        return (self.branches_covered / self.branches_valid) if self.branches_valid else 0.0


def parse_coverage(path: Path) -> Totals:
    tree = ET.parse(path)
    root = tree.getroot()
    t = Totals()

    # Root attributes: lines-valid, lines-covered, branches-valid, branches-covered
    def _get(attr: str) -> int:
        val = root.attrib.get(attr)
        try:
            return int(val) if val is not None else 0
        except Exception:
            return 0

    t.lines_valid = _get("lines-valid")
    t.lines_covered = _get("lines-covered")
    t.branches_valid = _get("branches-valid")
    t.branches_covered = _get("branches-covered")
    return t


def combine(inputs: list[Path]) -> Totals:
    total = Totals()
    for p in inputs:
        t = parse_coverage(p)
        total.lines_valid += t.lines_valid
        total.lines_covered += t.lines_covered
        total.branches_valid += t.branches_valid
        total.branches_covered += t.branches_covered
    return total


def write_combined_xml(t: Totals, out_xml: Path) -> None:
    # Minimal root with totals and rates
    root = ET.Element("coverage")
    root.set("lines-valid", str(t.lines_valid))
    root.set("lines-covered", str(t.lines_covered))
    root.set("line-rate", f"{t.line_rate:.4f}")
    root.set("branches-valid", str(t.branches_valid))
    root.set("branches-covered", str(t.branches_covered))
    root.set("branch-rate", f"{t.branch_rate:.4f}")
    ET.ElementTree(root).write(out_xml, encoding="utf-8", xml_declaration=True)


def write_summary_md(t: Totals, out_md: Path) -> None:
    percent = t.line_rate * 100.0
    bpercent = t.branch_rate * 100.0 if t.branches_valid else 0.0
    lines = [
        "# Coverage Summary",
        "",
        f"- Lines: {t.lines_covered}/{t.lines_valid} ({percent:.2f}%)",
        f"- Branches: {t.branches_covered}/{t.branches_valid} ({bpercent:.2f}%)",
    ]
    out_md.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inputs", nargs="+", required=True)
    ap.add_argument("--out-xml", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()

    inputs = [Path(p) for p in args.inputs]
    totals = combine(inputs)
    write_combined_xml(totals, Path(args.out_xml))
    write_summary_md(totals, Path(args.out_md))


if __name__ == "__main__":
    main()
