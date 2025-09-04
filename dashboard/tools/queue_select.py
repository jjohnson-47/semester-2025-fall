"""Now Queue selection via CP-SAT with graceful fallback.

Attempts to use OR-Tools CP-SAT; if unavailable, falls back to a
deterministic top-K selection that respects simple constraints.
"""

from __future__ import annotations

import os
from collections.abc import Iterable
from dataclasses import dataclass


@dataclass
class Candidate:
    id: str
    course: str | None
    score: float
    est_minutes: int | None
    is_chain_head: bool
    status: str


def _fallback_select(
    candidates: Iterable[Candidate],
    *,
    timebox: int,
    k: int,
    heavy_threshold: int,
    exclude_status: set[str] | None = None,
    min_courses: int | None = None,
    wip_cap: int | None = None,
) -> list[Candidate]:
    """Deterministic fallback: filter invalid, sort by score, take top-K within timebox & ≤1 heavy."""
    ex = exclude_status or {"done", "blocked"}
    pool = [c for c in candidates if c.status not in ex]
    pool.sort(key=lambda c: c.score, reverse=True)
    selected: list[Candidate] = []
    time_used = 0
    heavy_count = 0
    doing_count = 0
    courses = set()
    for c in pool:
        if len(selected) >= k:
            break
        minutes = int(c.est_minutes or 0)
        is_heavy = minutes >= heavy_threshold
        if time_used + minutes > timebox:
            continue
        if is_heavy and heavy_count >= 1:
            continue
        # WIP cap
        if wip_cap is not None and c.status == "doing" and doing_count >= wip_cap:
            continue
        selected.append(c)
        time_used += minutes
        if is_heavy:
            heavy_count += 1
        if c.status == "doing":
            doing_count += 1
        courses.add(c.course)
    # Try to satisfy min_courses by swapping if needed (greedy)
    if min_courses and len([cr for cr in courses if cr]) < min_courses:
        # Do nothing in fallback if infeasible
        pass
    return selected


def select_now_queue(
    candidates: Iterable[Candidate],
    *,
    timebox: int = 90,
    k: int = 3,
    heavy_threshold: int = 60,
    require_chain_heads: bool = True,
    min_courses: int | None = None,
    exclude_status: set[str] | None = None,
    wip_cap: int | None = None,
) -> list[Candidate]:
    """Select Now Queue using CP-SAT if available, otherwise fallback.

    Constraints:
    - Sum(est_minutes) ≤ timebox
    - ≤1 heavy (est_minutes ≥ heavy_threshold)
    - Exclude status in {done, blocked}
    - Optionally require chain heads unless queue would be empty (enforced inside solver phase)
    """
    # Feature flag: allow forcing fallback even if OR-Tools is installed
    use_cpsat = os.environ.get("PRIO_USE_CPSAT", "1").lower() not in {"0", "false", "no"}
    try:
        if not use_cpsat:
            raise ImportError("PRIO_USE_CPSAT disabled")
        from ortools.sat.python import cp_model  # type: ignore
    except Exception:
        return _fallback_select(
            candidates,
            timebox=timebox,
            k=k,
            heavy_threshold=heavy_threshold,
            exclude_status=exclude_status,
            min_courses=min_courses,
        )

    ex = exclude_status or {"done", "blocked"}
    cand = [c for c in candidates if c.status not in ex]
    if require_chain_heads and any(c.is_chain_head for c in cand):
        cand = [c for c in cand if c.is_chain_head]

    # Edge: empty → return empty
    if not cand:
        return []

    model = cp_model.CpModel()
    x = {c.id: model.NewBoolVar(c.id) for c in cand}

    # K items
    model.Add(sum(x.values()) <= k)

    # Timebox
    model.Add(sum(int(c.est_minutes or 0) * x[c.id] for c in cand) <= int(timebox))

    # ≤1 heavy
    model.Add(sum(x[c.id] for c in cand if int(c.est_minutes or 0) >= heavy_threshold) <= 1)

    # Distinct courses ≥ min_courses if requested and feasible
    courses: dict[str | None, list] = {}
    for c in cand:
        courses.setdefault(c.course, []).append(c)
    if min_courses and len([c for c in courses if c]) >= min_courses:
        # Introduce boolean vars indicating if any task of a course is selected
        course_sel = {}
        for course, items in courses.items():
            if not course:
                continue
            b = model.NewBoolVar(f"course_{course}")
            course_sel[course] = b
            model.Add(sum(x[i.id] for i in items) >= 1).OnlyEnforceIf(b)
            model.Add(sum(x[i.id] for i in items) == 0).OnlyEnforceIf(b.Not())
        if course_sel:
            model.Add(sum(course_sel.values()) >= min_courses)

    # WIP cap for doing status
    if wip_cap is not None:
        model.Add(sum(x[c.id] for c in cand if c.status == "doing") <= int(wip_cap))

    # Objective: maximize Σ(score*100)
    model.Maximize(sum(int(round(c.score * 100)) * x[c.id] for c in cand))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 0.05
    solver.parameters.num_search_workers = 8
    res = solver.Solve(model)

    if res not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return _fallback_select(
            cand,
            timebox=timebox,
            k=k,
            heavy_threshold=heavy_threshold,
            exclude_status=exclude_status,
            min_courses=min_courses,
            wip_cap=wip_cap,
        )

    return [c for c in cand if solver.Value(x[c.id]) == 1]
