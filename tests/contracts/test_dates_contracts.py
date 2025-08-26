#!/usr/bin/env python3
"""Contract test scaffold for date policies.

This does not enforce logic yet; it validates contract file structure so
future rule implementations can bind to these contracts.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import yaml  # type: ignore[import-untyped]


def _load_contracts(path: Path) -> Dict[str, Any]:
    data = yaml.safe_load(path.read_text())
    assert isinstance(data, dict)
    assert "contracts" in data
    assert isinstance(data["contracts"], list)
    return data


def test_dates_contracts_shape() -> None:
    path = Path("tests/contracts/dates.yaml")
    data = _load_contracts(path)
    for c in data["contracts"]:
        assert "name" in c and isinstance(c["name"], str)
        assert "rules" in c and isinstance(c["rules"], list)
