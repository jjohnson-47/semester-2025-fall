"""Prioritization service orchestrating DAG metrics, scoring v2, and solver.

This module uses the Database repo for tasks/ deps and persists scores and
now_queue. It exports a JSON now_queue for compatibility with the UI.
"""

from __future__ import annotations

import gzip
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from dashboard.db import Database
from dashboard.tools.contracts import load_constraints, load_factors, load_phase_weights, load_yaml
from dashboard.tools.dag import TaskDAG
from dashboard.tools.phase import detect_phase, load_semester_start, phase_weights
from dashboard.tools.queue_select import Candidate, select_now_queue
from dashboard.tools.scoring import score_task


@dataclass
class PrioritizationConfig:
    state_dir: Path
    calendar_path: Path
    semester_start_fallback: str = "2025-08-25"
    snapshot_rotate: int = 7


def _utcnow_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


class PrioritizationService:
    def __init__(self, db: Database, config: PrioritizationConfig) -> None:
        self.db = db
        self.config = config
        self.state_dir = config.state_dir
        self._contracts_path = Path("dashboard/tools/priority_contracts.yaml")
        self._contracts = load_yaml(self._contracts_path)

    # ------------------------------
    # Snapshots
    # ------------------------------
    def snapshot(self) -> None:
        """Snapshot DB and export JSON before major changes, keep last N."""
        snaps = self.state_dir / "snapshots"
        snaps.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Export JSON
        export_payload = self.db.export_tasks_json()
        with open(snaps / f"tasks_{ts}.json", "w") as f:
            json.dump(export_payload, f, indent=2)

        # Gzip DB raw file
        db_path = self.db.db_path
        if db_path.exists():
            with open(db_path, "rb") as fin, gzip.open(snaps / f"tasks_{ts}.db.gz", "wb") as fout:
                fout.write(fin.read())

        # Rotate
        files = sorted(snaps.glob("tasks_*.db.gz"))
        if len(files) > self.config.snapshot_rotate:
            for old in files[: -(self.config.snapshot_rotate)]:
                try:
                    old.unlink()
                except Exception as exc:  # pragma: no cover - best-effort
                    logging.getLogger(__name__).debug("Snapshot cleanup skipped: %s", exc)

    # ------------------------------
    # Phase
    # ------------------------------
    def _current_phase(self) -> tuple[str, dict[str, float]]:
        semester_start = load_semester_start(self.config.calendar_path)
        if not semester_start:
            # Fallback
            semester_start = datetime.strptime(
                self.config.semester_start_fallback, "%Y-%m-%d"
            ).date()  # type: ignore[arg-type]
        key = detect_phase(semester_start)
        weights = phase_weights(key)
        return key, weights

    # ------------------------------
    # DAG + Scoring + Solver
    # ------------------------------
    def refresh_now_queue(
        self,
        *,
        timebox: int = 90,
        k: int = 3,
        heavy_threshold: int | None = None,
        min_courses: int | None = None,
        include_courses: set[str] | None = None,
    ) -> list[str]:
        """Compute scores and select Now Queue; persist to DB and export JSON."""
        # Snapshot first
        self.snapshot()

        # Load data
        tasks = self.db.list_tasks()
        if include_courses:
            include_courses = {c for c in include_courses if c}
            tasks = [t for t in tasks if (t.get("course") or "") in include_courses]
        # Build deps list
        with self.db.connect() as conn:
            dep_rows = conn.execute("select task_id, blocks_id from deps").fetchall()
        deps = [(r["task_id"], r["blocks_id"]) for r in dep_rows]

        dag = TaskDAG(tasks, deps)
        cycle = dag.find_cycle()

        phase_key, _default_weights = self._current_phase()
        # Merge weights from contracts if present
        weights_map = load_phase_weights(self._contracts, phase_key)
        ctx = {"phase_weights": weights_map, "recent_completions": 0}

        # Compute metrics + score per task
        candidates: list[Candidate] = []
        score_map: dict[str, float] = {}
        metrics_map: dict[str, dict[str, Any]] = {}
        for t in tasks:
            tid = t["id"]
            status = t.get("status", "todo")
            # Metrics
            t_metrics = {
                "critical_depth": dag.critical_depth(tid),
                "downstream_unlocked": dag.downstream_unlocked(tid),
                "is_chain_head": dag.is_chain_head(tid),
                "anchor": bool(t.get("anchor")),
            }
            t_for_score = {**t, **t_metrics}

            # Weights from contracts (with safe defaults)
            weights = load_factors(self._contracts).weights
            total, contrib = score_task(t_for_score, ctx, weights)
            self.db.upsert_score(tid, total, contrib)
            score_map[tid] = float(total)
            metrics_map[tid] = t_metrics

            if status not in {"done", "blocked"}:
                candidates.append(
                    Candidate(
                        id=tid,
                        course=t.get("course"),
                        score=float(total),
                        est_minutes=int(t.get("est_minutes") or 0),
                        is_chain_head=bool(t_metrics["is_chain_head"]),
                        status=status,
                    )
                )

        # Select queue
        # Apply constraints from contracts
        cq = load_constraints(self._contracts)
        # Adjust min_courses if user restricted courses
        eff_min_courses = min_courses if min_courses is not None else cq.min_courses
        if include_courses:
            eff_min_courses = (
                min(eff_min_courses or 0, len(include_courses)) if eff_min_courses else None
            )

        selected = select_now_queue(
            candidates,
            timebox=timebox if timebox else (cq.fit_minutes or 90),
            k=k if k else (cq.k or 3),
            heavy_threshold=heavy_threshold if heavy_threshold is not None else cq.heavy_threshold,
            require_chain_heads=cq.require_chain_heads,
            min_courses=eff_min_courses,
            exclude_status=set(cq.exclude_status),
            wip_cap=cq.wip_cap,
        )
        queue_ids = [c.id for c in selected]
        self.db.set_now_queue(queue_ids)

        # Export JSON now_queue for the UI
        id_set = set(queue_ids)
        now_queue = []
        for t in tasks:
            if t["id"] in id_set:
                enriched = dict(t)
                enriched["smart_score"] = round(score_map.get(t["id"], 0.0), 2)
                m = metrics_map.get(t["id"], {})
                enriched["is_chain_head"] = bool(m.get("is_chain_head"))
                enriched["unblock_count"] = int(m.get("downstream_unlocked", 0))
                enriched["chain_distance"] = int(m.get("critical_depth", 0))
                # include immediate blockers list for UI upstream chip
                blockers = list(dag.blockers.get(t["id"], set()))
                if blockers:
                    enriched["depends_on"] = blockers
                now_queue.append(enriched)
        now_payload = {
            "queue": now_queue,
            "metadata": {
                "generated": datetime.now().isoformat(),
                "timebox": timebox,
                "phase": phase_key,
                "cycle": cycle,
            },
        }
        with open(self.state_dir / "now_queue.json", "w") as f:
            json.dump(now_payload, f, indent=2)

        return queue_ids

    def explain(self, task_id: str) -> dict[str, Any]:
        """Return score explanation; compute on the fly if missing."""
        t = self.db.get_task(task_id)
        if not t:
            return {"error": "Task not found"}

        # Full DAG context
        with self.db.connect() as conn:
            dep_rows = conn.execute("select task_id, blocks_id from deps").fetchall()
            task_rows = conn.execute("select * from tasks").fetchall()
        deps = [(r["task_id"], r["blocks_id"]) for r in dep_rows]
        all_tasks = [dict(r) for r in task_rows]
        dag = TaskDAG(all_tasks, deps)
        metrics = {
            "critical_depth": dag.critical_depth(task_id),
            "downstream_unlocked": dag.downstream_unlocked(task_id),
            "is_chain_head": dag.is_chain_head(task_id),
            "anchor": bool(t.get("anchor")),
        }
        phase_key, _ = self._current_phase()
        weights_map = load_phase_weights(self._contracts, phase_key)
        ctx = {"phase_weights": weights_map, "recent_completions": 0}
        weights = load_factors(self._contracts).weights
        total, contrib = score_task({**t, **metrics}, ctx, weights)
        explain = sorted(
            ({"factor": k, "contrib": round(v, 2)} for k, v in contrib.items()),
            key=lambda x: abs(x["contrib"]),
            reverse=True,
        )

        # minimal cut
        cut = dag.minimal_unblocking_cut(task_id, k=2)

        return {
            "task_id": task_id,
            "score": round(total, 2),
            "factors": contrib,
            "explain": explain,
            "minimal_unblock": cut,
            "phase": phase_key,
        }

    def health(self) -> dict[str, Any]:
        tasks = self.db.list_tasks()
        with self.db.connect() as conn:
            dep_rows = conn.execute("select task_id, blocks_id from deps").fetchall()
            score_row = conn.execute("select max(computed_at) as last from scores").fetchone()
        dag = TaskDAG(tasks, [(r["task_id"], r["blocks_id"]) for r in dep_rows])
        cycle = dag.find_cycle()
        suggestion = None
        if cycle:
            # Choose the cycle node whose blocking has the least downstream impact
            try:
                impacts = [(tid, dag.downstream_unlocked(tid)) for tid in cycle]
                impacts.sort(key=lambda kv: kv[1])
                suggestion = impacts[0][0] if impacts else cycle[0]
            except Exception:
                suggestion = cycle[0]
        return {
            "db": self.db.health(),
            "dag_ok": cycle is None,
            "cycle_path": cycle,
            "break_suggestion": suggestion,
            "last_scoring": score_row["last"] if score_row and score_row["last"] else None,
        }
