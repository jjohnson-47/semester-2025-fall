#!/usr/bin/env python3
"""Smart Task Reprioritization Engine.

This module implements an intelligent task prioritization system that goes beyond
simple due dates to identify the most impactful work. It computes a smart_score
based on critical chain analysis, unblock impact, anchor proximity, and phase-aware
category biases.

The system identifies "chain heads" (next actionable tasks) and produces a focused
"Now Queue" of the most important tasks to work on immediately.

Usage:
    python reprioritize.py --tasks tasks.json --contracts priority_contracts.yaml --write
"""

import argparse
import json
import logging
import sys
from collections import defaultdict, deque
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class TaskGraph:
    """Dependency graph for task analysis."""

    def __init__(self, tasks: list[dict[str, Any]]) -> None:
        """Initialize graph from task list."""
        self.tasks = {t["id"]: t for t in tasks}
        self.dependents: dict[str, list[str]] = defaultdict(list)
        self.dependencies: dict[str, list[str]] = defaultdict(list)

        # Build dependency maps
        for task in tasks:
            task_id = task["id"]
            for dep_id in task.get("depends_on", []):
                if dep_id in self.tasks:  # Only valid dependencies
                    self.dependencies[task_id].append(dep_id)
                    self.dependents[dep_id].append(task_id)

    def get_blocked_descendants(self, task_id: str) -> set[str]:
        """Get all tasks blocked downstream of this task."""
        visited = set()
        queue = deque([task_id])
        descendants = set()

        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)

            for dependent in self.dependents.get(current, []):
                task = self.tasks.get(dependent)
                if task and task.get("status") == "blocked":
                    descendants.add(dependent)
                queue.append(dependent)

        return descendants

    def find_anchors(self, anchor_configs: list[dict[str, Any]]) -> set[str]:
        """Identify anchor tasks based on configuration."""
        anchors = set()

        for config in anchor_configs:
            if "id" in config:
                # Exact ID match
                if config["id"] in self.tasks:
                    anchors.add(config["id"])
            elif "id_suffix" in config:
                # Suffix match
                suffix = config["id_suffix"]
                for task_id in self.tasks:
                    if task_id.endswith(suffix):
                        anchors.add(task_id)

        return anchors

    def compute_chain_weight(
        self, task_id: str, anchors: set[str], distance_decay: float = 0.95
    ) -> tuple[float, int, str | None]:
        """Compute critical chain weight from task to nearest anchor.

        Returns:
            (weight, distance, anchor_id)
        """
        if task_id in anchors:
            task = self.tasks[task_id]
            return (task.get("weight", 1), 0, task_id)

        # BFS to find paths to all anchors
        queue = deque([(task_id, 0, task.get("weight", 1)) for task in [self.tasks[task_id]]])
        visited = {task_id}
        best_weight = 0
        best_distance = float("inf")
        best_anchor = None

        while queue:
            current_id, distance, path_weight = queue.popleft()

            # Check if we reached an anchor
            if current_id in anchors:
                # Apply distance decay
                adjusted_weight = path_weight * (distance_decay**distance)
                if adjusted_weight > best_weight or (
                    adjusted_weight == best_weight and distance < best_distance
                ):
                    best_weight = adjusted_weight
                    best_distance = distance
                    best_anchor = current_id
                continue

            # Explore dependents
            for dependent_id in self.dependents.get(current_id, []):
                if dependent_id not in visited:
                    visited.add(dependent_id)
                    dep_task = self.tasks.get(dependent_id)
                    if dep_task and dep_task.get("status") != "done":
                        new_weight = path_weight + dep_task.get("weight", 1)
                        queue.append((dependent_id, distance + 1, new_weight))

        return (
            float(best_weight),
            int(best_distance) if best_distance != float("inf") else 999,
            best_anchor,
        )

    def is_chain_head(self, task_id: str) -> bool:
        """Check if task is a chain head (all dependencies completed)."""
        task = self.tasks.get(task_id)
        if not task:
            return False

        # Must be in todo status
        if task.get("status") != "todo":
            return False

        # All dependencies must be done
        for dep_id in self.dependencies.get(task_id, []):
            dep_task = self.tasks.get(dep_id)
            if dep_task and dep_task.get("status") != "done":
                return False

        return True


class SmartPrioritizer:
    """Smart task prioritization engine."""

    def __init__(
        self, tasks: list[dict[str, Any]], contracts: dict[str, Any], semester_first_day: str
    ) -> None:
        """Initialize prioritizer with tasks and contracts."""
        self.tasks = tasks
        self.contracts = contracts
        self.semester_start = datetime.fromisoformat(semester_first_day)
        self.today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        self.graph = TaskGraph(tasks)

        # Load configuration
        self.coefficients = contracts.get("coefficients", {})
        self.phases = contracts.get("phases", {})
        self.anchors = self.graph.find_anchors(contracts.get("anchors", []))
        self.now_queue_config = contracts.get("now_queue", {})
        self.pins = contracts.get("pins", {})
        self.staleness = contracts.get("staleness", {})
        self.critical_path_config = contracts.get("critical_path", {})

        logger.info(f"Initialized with {len(tasks)} tasks, {len(self.anchors)} anchors")

    def get_current_phase(self) -> dict[str, Any] | None:
        """Determine the current semester phase.

        Interpretation of phase windows:
        - Each phase config defines a window in terms of days relative to the
          semester first day, where negative numbers are before the start and
          positive numbers are after. For example, week one is 1..7, launch
          week is -7..0.

        Previous implementation incorrectly used "days until start", which
        inverted the sign and misclassified pre‑semester days as post‑semester
        phases. We correct this by using days since start.
        """
        # Positive if today is after start, negative if before
        days_since_start = (self.today - self.semester_start).days

        for _phase_key, phase in self.phases.items():
            start_days = phase.get("start_days", -999)
            end_days = phase.get("end_days", 999)

            # Check if today falls within this phase window
            if start_days <= days_since_start <= end_days:
                return dict(phase)

        return None

    def calculate_base_priority(self, task: dict[str, Any]) -> float:
        """Calculate base priority from due date (existing logic)."""
        if "due_date" not in task:
            return 0

        try:
            due_date = datetime.fromisoformat(task["due_date"])
            days_until = (due_date - self.today).days

            if days_until < 0:  # Overdue
                return 100 + abs(days_until) * 2
            elif days_until == 0:  # Due today
                return 50
            elif days_until <= 3:  # Due soon
                return 20
            elif days_until <= 7:  # Due this week
                return 10
            else:
                return max(0, 5 - days_until / 7)  # Gradual decay
        except (ValueError, TypeError):
            return 0

    def calculate_staleness_penalty(self, task: dict[str, Any]) -> float:
        """Calculate penalty for tasks that have been todo too long."""
        if not self.staleness.get("enabled", False):
            return 0

        if task.get("status") != "todo":
            return 0

        # Check when task became todo (use updated_at as proxy)
        try:
            updated = datetime.fromisoformat(task.get("updated_at", task.get("created_at", "")))
            days_in_todo = (self.today - updated).days

            threshold = self.staleness.get("days_until_stale", 14)
            if days_in_todo <= threshold:
                return 0

            days_stale = days_in_todo - threshold
            penalty = days_stale * self.staleness.get("stale_penalty", -5.0)
            max_penalty = self.staleness.get("max_penalty", -50.0)

            return float(max(penalty, max_penalty))
        except (ValueError, TypeError):
            return 0

    def is_pinned(self, task_id: str) -> bool:
        """Check if task is pinned."""
        if not self.pins:
            return False

        # Check exact ID pins
        by_id = self.pins.get("by_id", [])
        if by_id and task_id in by_id:
            return True

        # Check suffix pins
        by_suffix = self.pins.get("by_suffix", [])
        if by_suffix:
            for suffix in by_suffix:
                if task_id.endswith(suffix):
                    return True

        return False

    def calculate_smart_score(self, task: dict[str, Any]) -> dict[str, Any]:
        """Calculate comprehensive smart score for a task."""
        task_id = task["id"]
        scores = {}

        # 1. Base priority from due dates
        base_priority = self.calculate_base_priority(task)
        scores["base_priority"] = base_priority * self.coefficients.get("alpha_due", 1.0)

        # 2. Critical chain weight
        chain_weight, chain_distance, chain_anchor = self.graph.compute_chain_weight(
            task_id,
            self.anchors,
            self.critical_path_config.get("distance_decay", 0.95),
        )
        scores["chain_weight"] = chain_weight * self.coefficients.get("beta_critical", 2.5)

        # 3. Unblock impact
        blocked_descendants = self.graph.get_blocked_descendants(task_id)
        unblock_impact = len(blocked_descendants)
        scores["unblock_impact"] = unblock_impact * self.coefficients.get("gamma_impact", 3.0)

        # 4. Anchor proximity
        if chain_distance < 999:
            proximity_score = 1.0 / (chain_distance + 1)
            scores["anchor_proximity"] = (
                proximity_score * self.coefficients.get("delta_proximity", 1.5) * 10
            )
        else:
            scores["anchor_proximity"] = 0

        # 5. Chain head boost
        is_head = self.graph.is_chain_head(task_id)
        if is_head:
            scores["chain_head_boost"] = self.coefficients.get("epsilon_head", 10.0)
        else:
            scores["chain_head_boost"] = 0

        # 6. Phase and category adjustments
        current_phase = self.get_current_phase()
        if current_phase:
            category = task.get("category", "").lower()
            category_boost = current_phase.get("category_boosts", {}).get(category, 1.0)
            scores["phase_category"] = category_boost * self.coefficients.get("zeta_phase", 0.5)
        else:
            scores["phase_category"] = 0

        # 7. Staleness penalty
        scores["staleness"] = self.calculate_staleness_penalty(task)

        # 8. Pin boost
        if self.is_pinned(task_id):
            scores["pin_boost"] = self.pins.get("pin_boost", 100.0)
        else:
            scores["pin_boost"] = 0

        # Calculate total
        total_score = sum(scores.values())

        # Store results in task
        task["smart_score"] = round(total_score, 2)
        task["is_chain_head"] = is_head
        task["chain_anchor"] = chain_anchor
        task["chain_distance"] = chain_distance if chain_distance < 999 else None
        task["unblock_count"] = unblock_impact

        if self.contracts.get("debug", {}).get("include_score_breakdown", True):
            task["score_breakdown"] = {k: round(v, 2) for k, v in scores.items()}

        return task

    def build_now_queue(self) -> list[dict[str, Any]]:
        """Build the Now Queue of most important tasks."""
        # Filter to actionable tasks
        actionable = [
            t
            for t in self.tasks
            if t.get("status") in ["todo", "in_progress"]
            and not t.get("parent_id")  # Skip subtasks
        ]

        # Score all actionable tasks
        for task in actionable:
            self.calculate_smart_score(task)

        # Sort by smart score
        actionable.sort(key=lambda t: t.get("smart_score", 0), reverse=True)

        # Build queue with constraints
        queue = []
        course_counts: dict[str, int] = defaultdict(int)
        max_items = self.now_queue_config.get("max_items", 7)
        per_course_limit = self.now_queue_config.get("per_course_limit", 3)
        ensure_each = self.now_queue_config.get("ensure_each_course", True)

        # First pass: ensure one from each course if required
        if ensure_each:
            courses_seen = set()
            for task in actionable:
                course = task.get("course")
                if course and course not in courses_seen:
                    queue.append(task)
                    course_counts[course] += 1
                    courses_seen.add(course)
                    if len(queue) >= max_items:
                        break

        # Second pass: fill remaining slots, preferring chain heads
        chain_head_pref = self.now_queue_config.get("chain_head_preference", 1.2)

        for task in actionable:
            if len(queue) >= max_items:
                break

            if task in queue:
                continue

            course = task.get("course")
            if course and course_counts.get(course, 0) >= per_course_limit:
                continue

            # Boost chain heads for queue selection
            effective_score = task.get("smart_score", 0)
            if task.get("is_chain_head"):
                effective_score *= chain_head_pref

            # Add to queue
            queue.append(task)
            if course:
                course_counts[course] = course_counts.get(course, 0) + 1

        # Sort queue by score for display
        queue.sort(key=lambda t: t.get("smart_score", 0), reverse=True)

        return queue

    def process(self) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Process all tasks and return updated tasks and now queue."""
        # Log current phase once
        current_phase = self.get_current_phase()
        if current_phase:
            logger.info(f"Current phase: {current_phase.get('name', 'Unknown')}")

        # Score all tasks
        for task in self.tasks:
            if task.get("status") != "done":
                self.calculate_smart_score(task)

        # Build now queue
        now_queue = self.build_now_queue()

        # Log summary
        logger.info(f"Scored {len(self.tasks)} tasks")
        logger.info(f"Now Queue: {len(now_queue)} tasks")
        for i, task in enumerate(now_queue[:5], 1):
            logger.info(
                f"  {i}. {task['id']}: {task.get('smart_score', 0):.1f} "
                f"{'[HEAD]' if task.get('is_chain_head') else ''}"
            )

        return self.tasks, now_queue


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Smart task reprioritization")
    parser.add_argument("--tasks", required=True, help="Path to tasks.json")
    parser.add_argument("--contracts", required=True, help="Path to priority_contracts.yaml")
    parser.add_argument(
        "--semester-first-day", default="2025-08-25", help="Semester start date (YYYY-MM-DD)"
    )
    parser.add_argument("--write", action="store_true", help="Write results back to files")
    parser.add_argument("--now-queue-only", action="store_true", help="Only output now queue")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Load tasks
    tasks_path = Path(args.tasks)
    if not tasks_path.exists():
        logger.error(f"Tasks file not found: {tasks_path}")
        sys.exit(1)

    with open(tasks_path) as f:
        tasks_data = json.load(f)

    # Load contracts
    contracts_path = Path(args.contracts)
    if not contracts_path.exists():
        logger.error(f"Contracts file not found: {contracts_path}")
        sys.exit(1)

    with open(contracts_path) as f:
        contracts = yaml.safe_load(f)

    # Process tasks
    prioritizer = SmartPrioritizer(tasks_data.get("tasks", []), contracts, args.semester_first_day)
    updated_tasks, now_queue = prioritizer.process()

    # Update tasks data
    tasks_data["tasks"] = updated_tasks
    tasks_data["metadata"]["reprioritized"] = datetime.now().isoformat()

    # Prepare now queue data
    now_queue_data = {
        "queue": now_queue,
        "metadata": {
            "generated": datetime.now().isoformat(),
            "phase": prioritizer.get_current_phase(),
            "total_tasks": len(updated_tasks),
            "actionable_tasks": sum(1 for t in updated_tasks if t.get("status") == "todo"),
        },
    }

    if args.write:
        # Write updated tasks
        with open(tasks_path, "w") as f:
            json.dump(tasks_data, f, indent=2)
        logger.info(f"Updated tasks written to {tasks_path}")

        # Write now queue
        now_queue_path = tasks_path.parent / "now_queue.json"
        with open(now_queue_path, "w") as f:
            json.dump(now_queue_data, f, indent=2)
        logger.info(f"Now queue written to {now_queue_path}")
    else:
        # Output to console
        if args.now_queue_only:
            print(json.dumps(now_queue_data, indent=2))
        else:
            print("NOW QUEUE:")
            print("=" * 60)
            for i, task in enumerate(now_queue[:10], 1):
                status_icon = "➜" if task.get("is_chain_head") else "○"
                title = task.get("title", "")[:50] if task.get("title") else "No title"
                due_date = task.get("due_date", "N/A")
                due_date_str = due_date[:10] if due_date != "N/A" else "N/A"
                print(
                    f"{i:2}. {status_icon} [{task.get('course')}] {title}"
                    f"\n     Score: {task.get('smart_score', 0):.1f} | "
                    f"Due: {due_date_str} | "
                    f"Unblocks: {task.get('unblock_count', 0)}"
                )
                if task.get("chain_anchor"):
                    print(f"     → {task['chain_anchor']}")
            print("=" * 60)


if __name__ == "__main__":
    main()
