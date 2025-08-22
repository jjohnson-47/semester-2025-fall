"""Tests for semester phase detection in SmartPrioritizer.

Validates mapping of dates around the semester start to configured phases.
"""

from datetime import datetime, timedelta
from typing import Any

import pytest

# Import directly from the reprioritizer tool
from dashboard.tools.reprioritize import SmartPrioritizer


def build_contracts() -> dict[str, Any]:
    """Return a minimal contracts dict with phase definitions."""
    return {
        "phases": {
            "prelaunch": {
                "name": "Pre-Launch",
                "start_days": -30,
                "end_days": -8,
                "category_boosts": {},
            },
            "launch_week": {
                "name": "Launch Week",
                "start_days": -7,
                "end_days": 0,
                "category_boosts": {},
            },
            "week_one": {
                "name": "Week One",
                "start_days": 1,
                "end_days": 7,
                "category_boosts": {},
            },
            "in_term": {
                "name": "In Term",
                "start_days": 8,
                "end_days": 120,
                "category_boosts": {},
            },
        }
    }


@pytest.mark.parametrize(
    "offset_days,expected_name",
    [
        (-26, "Pre-Launch"),  # clearly before start
        (-5, "Launch Week"),  # within launch window
        (1, "Week One"),  # first day after start
        (11, "In Term"),  # well into term
    ],
)
def test_phase_detection_across_windows(offset_days: int, expected_name: str) -> None:
    """Ensure get_current_phase returns the correct configured phase name."""
    semester_first_day = "2025-08-25"
    contracts = build_contracts()
    tasks: list[dict[str, Any]] = []

    p = SmartPrioritizer(tasks, contracts, semester_first_day)

    # Override "today" to a deterministic date relative to start
    start_dt = datetime.fromisoformat(semester_first_day)
    p.today = start_dt + timedelta(days=offset_days)

    phase = p.get_current_phase()
    assert phase is not None, "Phase should not be None for tested windows"
    assert phase.get("name") == expected_name
