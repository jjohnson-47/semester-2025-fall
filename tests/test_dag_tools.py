#!/usr/bin/env python3
"""
Unit tests for dashboard.tools.dag.TaskDAG.
"""

from __future__ import annotations

from dashboard.tools.dag import TaskDAG


def make_tasks():
    tasks = [
        {"id": "A", "status": "done", "anchor": True},
        {"id": "B", "status": "todo"},
        {"id": "C", "status": "todo"},
        {"id": "D", "status": "todo"},
    ]
    deps = [("B", "A"), ("C", "B"), ("D", "B")]
    return tasks, deps


def test_cycle_detection_and_chain_heads():
    tasks, deps = make_tasks()
    dag = TaskDAG(tasks, deps)
    assert dag.find_cycle() is None
    heads = dag.chain_heads()
    # B depends on A(done) → B is chain-head; C and D depend on B(todo) → not heads
    assert "B" in heads and "C" not in heads and "D" not in heads

    # Introduce a cycle B->C and C->B
    dag2 = TaskDAG(tasks, deps + [("B", "C")])
    cyc = dag2.find_cycle()
    assert cyc is not None and len(cyc) >= 2


def test_metrics_and_minimal_cut():
    tasks, deps = make_tasks()
    dag = TaskDAG(tasks, deps)
    # Critical depth from A (anchor) is 0, from B (leading to C/D) is ≥1
    assert dag.critical_depth("A") == 0
    # From B no anchor reachable via dependents edges in this DAG
    assert dag.critical_depth("B") == 0
    # Downstream unlocked from B should count C and D
    assert dag.downstream_unlocked("B") >= 2
    # Minimal cut for C (blocked by B) should include B
    cut = dag.minimal_unblocking_cut("C", k=1)
    assert cut == ["B"]
