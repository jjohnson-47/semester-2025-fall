#!/usr/bin/env python3
"""Coverage ratchet script.

Reads coverage.xml (coverage.py schema) and compares total line-rate against
the committed baseline in .ratchet/base_coverage.txt. Fails CI if coverage
drops by more than THRESH_DROP percentage points. Advances the baseline when
coverage improves by at least THRESH_DROP.
"""

from __future__ import annotations

import pathlib
import sys
import xml.etree.ElementTree as ET

THRESH_DROP = 0.5  # percent points
BASELINE_FILE = pathlib.Path(".ratchet/base_coverage.txt")


def read_total_from_xml(path: pathlib.Path) -> float:
    t = ET.parse(path).getroot()
    # coverage.py xml: <coverage line-rate="0.73" ...>
    rate = float(t.attrib.get("line-rate", "0.0"))
    return round(rate * 100, 2)


def read_baseline() -> float | None:
    if BASELINE_FILE.exists():
        return float(BASELINE_FILE.read_text().strip())
    # No baseline: set to current to avoid first-run failure
    return None


def main(xml_path: str) -> int:
    xml_p = pathlib.Path(xml_path)
    if not xml_p.exists():
        print(f"coverage xml not found at: {xml_p}")
        return 0
    current = read_total_from_xml(xml_p)
    baseline = read_baseline()
    print(f"Current coverage: {current:.2f}%")
    if baseline is None:
        print("No baseline file; treating current as baseline.")
        BASELINE_FILE.parent.mkdir(parents=True, exist_ok=True)
        BASELINE_FILE.write_text(f"{current:.2f}\n")
        return 0
    print(f"Baseline coverage: {baseline:.2f}% (allowed drop ≤ {THRESH_DROP}pp)")
    if current + 1e-9 < baseline - THRESH_DROP:
        print(f"ERROR: coverage dropped by {baseline - current:.2f}pp > {THRESH_DROP}pp")
        return 1
    # If improved by ≥0.5pp, advance baseline
    if current > baseline + THRESH_DROP - 1e-9:
        BASELINE_FILE.write_text(f"{current:.2f}\n")
        print(f"Advanced baseline to {current:.2f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "coverage.xml"))
