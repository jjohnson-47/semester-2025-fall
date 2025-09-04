"""Priority contracts loader.

Loads weights, constraints, and phase category weights from YAML.
Provides safe defaults if file is missing or partially defined.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml  # type: ignore[import-untyped]


@dataclass
class FactorWeights:
    weights: Dict[str, float]


@dataclass
class NowQueueConstraints:
    k: int = 3
    max_heavy: int = 1
    min_courses: int = 2
    exclude_status: tuple[str, ...] = ("done", "blocked")
    fit_minutes: int = 90
    require_chain_heads: bool = True
    heavy_threshold: int = 60
    wip_cap: Optional[int] = 3


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


def load_factors(doc: dict[str, Any]) -> FactorWeights:
    section = (doc.get("factors") or {})
    weights = {k: float(v.get("weight", 0.0)) for k, v in section.items() if isinstance(v, dict)}
    # Provide defaults if empty
    if not weights:
        weights = {
            "due_urgency": 1.0,
            "critical_path": 2.5,
            "unblock_impact": 3.0,
            "anchor_proximity": 1.5,
            "chain_head_boost": 10.0,
            "phase_category": 0.5,
            "cost_of_delay": 2.0,
            "freshness_decay": 1.0,
            "momentum_bonus": 0.8,
        }
    return FactorWeights(weights)


def load_constraints(doc: dict[str, Any]) -> NowQueueConstraints:
    s = (doc.get("constraints") or {}).get("now_queue") or {}
    return NowQueueConstraints(
        k=int(s.get("k", 3)),
        max_heavy=int(s.get("max_heavy", 1)),
        min_courses=int(s.get("min_courses", 2)),
        exclude_status=tuple(s.get("exclude_status", ["done", "blocked"])),
        fit_minutes=int(s.get("fit_minutes", 90)),
        require_chain_heads=bool(s.get("require_chain_heads", True)),
        heavy_threshold=int(s.get("heavy_threshold", 60)),
        wip_cap=int(s.get("wip_cap", 3)) if s.get("wip_cap") is not None else None,
    )


def load_phase_weights(doc: dict[str, Any], phase_key: str) -> Dict[str, float]:
    phase_map = doc.get("phase") or {}
    if phase_key in phase_map:
        return {k: float(v) for k, v in (phase_map[phase_key] or {}).items()}
    # fallback defaults align with phase.py
    from .phase import phase_weights

    return phase_weights(phase_key)
