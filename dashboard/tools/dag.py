"""DAG utilities: build graph, detect cycles, compute metrics.

Operates on a tasks list (id, status, category, anchor, etc.) and a deps list
(task_id, blocks_id). Provides:
- cycle detection (returns a simple cycle path if present)
- chain heads (next actionable tasks with all blockers done)
- critical depth (longest hop count to any anchor)
- downstream unlocked (count of reachable tasks)
- minimal unblocking cut suggestion for a blocked task
"""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple


class TaskDAG:
    def __init__(self, tasks: Iterable[Dict[str, Any]], deps: Iterable[Tuple[str, str]]) -> None:
        self.tasks: Dict[str, Dict[str, Any]] = {t["id"]: dict(t) for t in tasks if t.get("id")}
        self.blockers: Dict[str, Set[str]] = defaultdict(set)
        self.dependents: Dict[str, Set[str]] = defaultdict(set)
        for task_id, blocks_id in deps:
            if task_id in self.tasks and blocks_id in self.tasks:
                self.blockers[task_id].add(blocks_id)
                self.dependents[blocks_id].add(task_id)

    # ------------------------------
    # Cycle detection
    # ------------------------------
    def find_cycle(self) -> Optional[List[str]]:
        """Return a cycle path (list of ids) if present, else None."""
        color: Dict[str, int] = {tid: 0 for tid in self.tasks}  # 0=unseen,1=visiting,2=done
        parent: Dict[str, Optional[str]] = {tid: None for tid in self.tasks}

        def dfs(u: str) -> Optional[List[str]]:
            color[u] = 1
            for v in self.dependents.get(u, set()):
                if color[v] == 0:
                    parent[v] = u
                    cyc = dfs(v)
                    if cyc:
                        return cyc
                elif color[v] == 1:
                    # Found back-edge u->v; reconstruct cycle
                    path = [v]
                    cur = u
                    while cur != v and cur is not None:
                        path.append(cur)
                        cur = parent[cur]
                    path.reverse()
                    return path
            color[u] = 2
            return None

        for nid in self.tasks:
            if color[nid] == 0:
                cyc = dfs(nid)
                if cyc:
                    return cyc
        return None

    # ------------------------------
    # Chain heads
    # ------------------------------
    def is_chain_head(self, task_id: str) -> bool:
        t = self.tasks.get(task_id)
        if not t or t.get("status") not in {"todo", "doing", "in_progress"}:
            return False
        for b in self.blockers.get(task_id, set()):
            bt = self.tasks.get(b)
            if bt and bt.get("status") != "done":
                return False
        return True

    def chain_heads(self) -> Set[str]:
        return {tid for tid in self.tasks if self.is_chain_head(tid)}

    # ------------------------------
    # Metrics
    # ------------------------------
    def anchors(self) -> Set[str]:
        return {tid for tid, t in self.tasks.items() if t.get("anchor")}

    def critical_depth(self, start: str) -> int:
        """Longest hop distance from start to any anchor along dependents edges."""
        A = self.anchors()
        if not A:
            return 0
        best = 0
        q: deque[Tuple[str, int]] = deque([(start, 0)])
        seen: Set[str] = set()
        while q:
            u, d = q.popleft()
            if u in seen:
                continue
            seen.add(u)
            if u in A:
                best = max(best, d)
            for v in self.dependents.get(u, set()):
                q.append((v, d + 1))
        return best

    def downstream_unlocked(self, start: str) -> int:
        """Count of tasks reachable downstream from start (dependents closure)."""
        cnt = 0
        q: deque[str] = deque([start])
        seen: Set[str] = set()
        while q:
            u = q.popleft()
            if u in seen:
                continue
            seen.add(u)
            for v in self.dependents.get(u, set()):
                cnt += 1
                q.append(v)
        return cnt

    # ------------------------------
    # Minimal unblocking cut (greedy)
    # ------------------------------
    def minimal_unblocking_cut(self, task_id: str, k: int = 2) -> List[str]:
        """Suggest up to k blockers whose completion unlocks the most downstream tasks (greedy)."""
        blockers = list(self.blockers.get(task_id, set()))
        if not blockers:
            return []
        scores = [(b, self.downstream_unlocked(b)) for b in blockers]
        scores.sort(key=lambda kv: kv[1], reverse=True)
        return [b for b, _ in scores[:k]]

