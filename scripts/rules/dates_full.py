"""Compatibility facade for DateRules (pre-refactor path).

Bridges the feature branch API to the current rules engine implementation by
re-exporting the modern DateRules and providing matching enum/dataclass types.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

# Reuse AssignmentType from the unified models
from scripts.rules.models import AssignmentType  # noqa: F401
from scripts.rules.dates import DateRules as _DateRules


class ShiftDirection(Enum):
  EARLIER = "earlier"
  LATER = "later"
  NEAREST = "nearest"


@dataclass
class DateShift:
  original: datetime
  shifted: datetime
  reason: str
  rule: str


class DateRules(_DateRules):  # type: ignore[misc]
  """Subclass for compatibility; inherits full functionality from current rules.

  This preserves import paths used by the feature branch while relying on the
  consolidated implementation in `scripts/rules/dates.py`.
  """

  # No additional behavior needed; all features are in the parent implementation.
  pass

