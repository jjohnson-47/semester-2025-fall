#!/usr/bin/env python3
"""
Unit tests for phase utilities and priority contracts loader.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from dashboard.tools.contracts import load_constraints, load_factors, load_phase_weights, load_yaml
from dashboard.tools.phase import detect_phase, load_semester_start, phase_weights


def test_detect_phase_ranges() -> None:
    start = date(2025, 8, 25)
    assert detect_phase(start, today=date(2025, 8, 10)) == "pre_launch"
    assert detect_phase(start, today=date(2025, 8, 25)) == "launch_week"
    assert detect_phase(start, today=date(2025, 8, 26)) == "week_one"
    assert detect_phase(start, today=date(2025, 9, 15)) == "in_term"


def test_load_semester_start(tmp_path: Path) -> None:
    cal = tmp_path / "calendar.json"
    cal.write_text(json.dumps({"semester_start": "2025-08-25"}))
    d = load_semester_start(cal)
    assert d == date(2025, 8, 25)


def test_phase_weights_defaults_and_overrides() -> None:
    w = phase_weights("in_term")
    assert "assessment" in w and w["assessment"] >= 2.0


def test_contracts_loader() -> None:
    # Use the provided YAML
    from pathlib import Path

    p = Path("dashboard/tools/priority_contracts.yaml")
    doc = load_yaml(p)
    f = load_factors(doc)
    assert "due_urgency" in f.weights and f.weights["chain_head_boost"] > 0.0
    c = load_constraints(doc)
    assert c.k >= 1 and c.fit_minutes >= 60
    wmap = load_phase_weights(doc, "in_term")
    assert wmap.get("assessment", 0) > 0
