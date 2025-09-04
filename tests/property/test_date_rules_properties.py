#!/usr/bin/env python3
from __future__ import annotations

import pytest

pytest.importorskip("hypothesis")
import hypothesis.strategies as st  # type: ignore
from hypothesis import given  # type: ignore

from scripts.rules.dates import DateRules


@given(
    label=st.text(min_size=1, max_size=50),
    is_assessment=st.booleans(),
    holidays=st.lists(st.sampled_from(["Labor Day", "Fall Break", "Non-Teaching Day"]), max_size=2),
    weekday=st.sampled_from([0, 1, 2, 3, 4, 5, 6]),
)
def test_apply_holiday_shift_avoids_weekends(label: str, is_assessment: bool, holidays: list[str], weekday: int) -> None:
    wd, add = DateRules.apply_holiday_shift(weekday, holidays, label, is_assessment)
    # Ensure final weekday is not Sat/Sun
    assert wd not in (5, 6)
