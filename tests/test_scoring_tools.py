#!/usr/bin/env python3
"""
Unit tests for scoring and selection tools.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

from dashboard.tools.scoring import cost_of_delay, freshness_decay, score_task
from dashboard.tools.queue_select import Candidate, select_now_queue


def test_cost_of_delay_and_freshness_decay() -> None:
  now = datetime(2025, 8, 20, tzinfo=timezone.utc)
  near = now + timedelta(days=1)
  far = now + timedelta(days=30)
  assert cost_of_delay(near, now) > cost_of_delay(far, now)

  old = now - timedelta(days=21)
  dec = freshness_decay(old, now)
  assert dec == -3.0 or dec <= -3.0  # capped at -3


def test_score_task_contributions_sum() -> None:
  task = {
    "due_at": (datetime.utcnow() + timedelta(days=3)).isoformat(),
    "critical_depth": 2,
    "downstream_unlocked": 5,
    "anchor": True,
    "is_chain_head": True,
    "category": "assessment",
    "last_touched": (datetime.utcnow() - timedelta(days=1)).isoformat(),
  }
  ctx = {"phase_weights": {"assessment": 3.0}, "recent_completions": 5}
  weights = {
    "due_urgency": 1.0,
    "critical_path": 2.0,
    "unblock_impact": 1.0,
    "anchor_proximity": 1.0,
    "chain_head_boost": 1.0,
    "phase_category": 1.0,
    "cost_of_delay": 1.0,
    "freshness_decay": 1.0,
    "momentum_bonus": 1.0,
  }
  total, contrib = score_task(task, ctx, weights)
  assert isinstance(total, float)
  assert abs(sum(contrib.values()) - total) < 1e-6
  assert contrib["phase_category"] > 0  # boosted by phase_weights


def test_select_now_queue_fallback_constraints() -> None:
  # Force fallback
  os.environ["PRIO_USE_CPSAT"] = "0"
  cands = [
    Candidate(id="A", course="X", score=10.0, est_minutes=30, is_chain_head=True, status="todo"),
    Candidate(id="B", course="Y", score=9.0, est_minutes=70, is_chain_head=True, status="todo"),
    Candidate(id="C", course="X", score=8.0, est_minutes=30, is_chain_head=True, status="doing"),
    Candidate(id="D", course="Z", score=7.0, est_minutes=30, is_chain_head=False, status="todo"),
  ]
  sel = select_now_queue(cands, timebox=90, k=3, heavy_threshold=60, min_courses=2, wip_cap=1)
  # Should respect constraints: timebox, ≤1 heavy, size ≤ k
  assert len(sel) <= 3
  total_minutes = sum(int(c.est_minutes or 0) for c in sel)
  assert total_minutes <= 90
  heavy = [c for c in sel if int(c.est_minutes or 0) >= 60]
  assert len(heavy) <= 1
