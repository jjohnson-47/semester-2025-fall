"""Phase auto-detection utilities.

Derive current phase from semester anchors (e.g., semester_start).
Allows optional overrides. Returns a phase key and category weights map.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Dict, Optional, Tuple


@dataclass
class PhaseConfig:
    pre_launch: Tuple[int, int] = (-30, -8)
    launch_week: Tuple[int, int] = (-7, 0)
    week_one: Tuple[int, int] = (1, 7)
    in_term: Tuple[int, int] = (8, 120)


DEFAULT_WEIGHTS = {
    "pre_launch": {"assessment": 1.0, "communication": 1.0, "content": 1.2, "materials": 1.3, "technical": 1.5, "setup": 1.7},
    "launch_week": {"assessment": 1.5, "communication": 1.4, "content": 1.2, "materials": 1.0, "technical": 1.0, "setup": 1.0},
    "week_one": {"assessment": 1.7, "communication": 1.5, "content": 1.2, "materials": 1.0, "technical": 1.0, "setup": 0.8},
    "in_term": {"assessment": 3.0, "communication": 2.5, "content": 2.0, "materials": 1.5, "technical": 1.0, "setup": 0.5},
}


def _days_since(start: date, today: date) -> int:
    return (today - start).days


def detect_phase(semester_start: date, today: Optional[date] = None, phases: Optional[PhaseConfig] = None) -> str:
    """Return phase key for given date relative to semester_start."""
    phases = phases or PhaseConfig()
    t = today or date.today()
    ds = _days_since(semester_start, t)
    if phases.pre_launch[0] <= ds <= phases.pre_launch[1]:
        return "pre_launch"
    if phases.launch_week[0] <= ds <= phases.launch_week[1]:
        return "launch_week"
    if phases.week_one[0] <= ds <= phases.week_one[1]:
        return "week_one"
    return "in_term"


def load_semester_start(calendar_path: Path) -> Optional[date]:
    """Load semester_start date from a JSON calendar file if available."""
    if not calendar_path.exists():
        return None
    with open(calendar_path) as f:
        data = json.load(f)
    s = data.get("semester_start") or data.get("semester_first_day")
    if not s:
        return None
    try:
        return datetime.fromisoformat(s).date()
    except Exception:
        try:
            return datetime.strptime(s, "%Y-%m-%d").date()
        except Exception:
            return None


def phase_weights(phase_key: str, overrides: Optional[Dict[str, float]] = None) -> Dict[str, float]:
    weights = dict(DEFAULT_WEIGHTS.get(phase_key, DEFAULT_WEIGHTS["in_term"]))
    if overrides:
        weights.update(overrides)
    return weights

