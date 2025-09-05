"""Scoring v2: deterministic, explainable task scoring.

Implements factor computations with bounded ranges and returns both total score
and per-factor contributions. Stores no state; callers persist via repo layer.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from math import exp
from typing import Any

# ------------------------------
# Factor model
# ------------------------------


@dataclass
class Factors:
    due_urgency: float = 0.0
    critical_path: float = 0.0
    unblock_impact: float = 0.0
    anchor_proximity: float = 0.0
    chain_head_boost: float = 0.0
    phase_category: float = 0.0
    cost_of_delay: float = 0.0
    freshness_decay: float = 0.0
    momentum_bonus: float = 0.0

    def to_dict(self) -> dict[str, float]:
        return {
            "due_urgency": self.due_urgency,
            "critical_path": self.critical_path,
            "unblock_impact": self.unblock_impact,
            "anchor_proximity": self.anchor_proximity,
            "chain_head_boost": self.chain_head_boost,
            "phase_category": self.phase_category,
            "cost_of_delay": self.cost_of_delay,
            "freshness_decay": self.freshness_decay,
            "momentum_bonus": self.momentum_bonus,
        }


def sigmoid(x: float) -> float:
    return 1.0 / (1.0 + exp(-x))


def cost_of_delay(due_ts: datetime, now: datetime) -> float:
    """Convex penalty as due date nears (0..10)."""
    days = (due_ts - now).total_seconds() / 86400.0
    return max(0.0, 10.0 * (1.0 - sigmoid((days - 3.0) / 2.0)))


def freshness_decay(last_touched: datetime, now: datetime) -> float:
    """Decay -1 per week of staleness, capped at -3."""
    days = (now - last_touched).total_seconds() / 86400.0
    return -min(3.0, days / 7.0)


# ------------------------------
# Scoring
# ------------------------------


def score_task(
    task: dict[str, Any], ctx: dict[str, Any], weights: dict[str, float]
) -> tuple[float, dict[str, float]]:
    """Compute score and per-factor contributions for a task.

    Args:
        task: dict with fields like due_at, critical_depth, downstream_unlocked, anchor, is_chain_head, last_touched
        ctx: context containing phase_weights (category->multiplier) and recent_completions
        weights: factor weights by name

    Returns:
        total score, contribution map {factor_name: contribution}
    """
    now = datetime.now(UTC)
    factors = Factors()

    # Raw factor values (bounded)
    due_str = task.get("due_at") or task.get("due_date")
    if due_str:
        try:
            due_dt = datetime.fromisoformat(due_str)
            days = (due_dt - now).days
            factors.due_urgency = min(10.0, max(0.0, 10.0 - float(days)))
            factors.cost_of_delay = cost_of_delay(due_dt, now)
        except Exception:
            pass

    factors.critical_path = float(min(10.0, float(task.get("critical_depth") or 0.0)))
    factors.unblock_impact = float(min(10.0, float(task.get("downstream_unlocked") or 0.0)))
    factors.anchor_proximity = 10.0 if task.get("anchor") else 0.0
    factors.chain_head_boost = 10.0 if task.get("is_chain_head") else 0.0

    phase_weights = ctx.get("phase_weights") or {}
    category = (task.get("category") or "").lower()
    if category in phase_weights:
        # Center around ~0 by subtracting 1.0
        factors.phase_category = float(phase_weights[category]) - 1.0

    last_touched_str = task.get("last_touched") or task.get("updated_at")
    if last_touched_str:
        try:
            factors.freshness_decay = freshness_decay(datetime.fromisoformat(last_touched_str), now)
        except Exception as exc:  # pragma: no cover - parsing
            logging.getLogger(__name__).debug("freshness_decay parse skip: %s", exc)

    # Momentum based on recent completions in context (0..3)
    try:
        recent = float(ctx.get("recent_completions") or 0.0)
        factors.momentum_bonus = min(3.0, recent / 5.0)
    except Exception:
        pass

    # Contributions and total
    contrib = {
        name: factors.to_dict()[name] * float(weights.get(name, 0.0)) for name in factors.to_dict()
    }
    total = float(sum(contrib.values()))
    return total, contrib
