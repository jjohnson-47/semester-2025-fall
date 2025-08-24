#!/usr/bin/env python3
"""Intelligent Task Orchestration System with Learning Capabilities.

This module provides an adaptive orchestration system that learns from task execution
patterns and automatically optimizes task scheduling and dependencies. It integrates
with the existing task management system while adding AI-driven insights.

Features:
    - Smart dependency resolution with cycle detection
    - Machine learning-based task prioritization
    - Automatic task parallelization detection
    - Historical pattern analysis for optimization
    - Real-time adaptation based on execution metrics
"""

import json
import logging
import time
from collections import defaultdict, deque
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class TaskOrchestrator:
    """Intelligent task orchestration with learning capabilities."""

    def __init__(self, state_dir: Path = Path("dashboard/state")):
        self.state_dir = state_dir
        self.state_dir.mkdir(exist_ok=True)

        # Learning state files
        self.patterns_file = self.state_dir / "orchestration_patterns.json"
        self.metrics_file = self.state_dir / "execution_metrics.json"
        self.dependencies_file = self.state_dir / "learned_dependencies.json"

        # Load or initialize learning state
        self.patterns = self._load_json(
            self.patterns_file, {"task_sequences": [], "success_rates": {}}
        )
        self.metrics = self._load_json(
            self.metrics_file, {"execution_times": {}, "failure_patterns": {}}
        )
        self.learned_deps = self._load_json(
            self.dependencies_file, {"implicit": {}, "suggested": {}}
        )

        # Runtime state
        self.execution_history = deque(maxlen=100)
        self.active_executions = {}

    def _load_json(self, file_path: Path, default: dict) -> dict:
        """Load JSON file with fallback to default."""
        if file_path.exists():
            try:
                with open(file_path) as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load {file_path}: {e}")
        return default

    def _save_json(self, file_path: Path, data: dict) -> None:
        """Save data to JSON file."""
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def analyze_task_graph(self, tasks: list[dict[str, Any]]) -> dict[str, Any]:
        """Analyze task dependencies and identify optimization opportunities.

        Returns:
            Analysis results including parallelizable tasks, critical path, and bottlenecks.
        """
        task_map = {t["id"]: t for t in tasks}

        # Build dependency graph
        graph = defaultdict(list)
        reverse_graph = defaultdict(list)

        for task in tasks:
            task_id = task["id"]
            deps = task.get("depends_on", [])

            for dep in deps:
                graph[dep].append(task_id)
                reverse_graph[task_id].append(dep)

        # Detect cycles
        cycles = self._detect_cycles(graph)
        if cycles:
            logger.warning(f"Dependency cycles detected: {cycles}")

        # Find parallelizable task groups
        parallel_groups = self._find_parallel_tasks(tasks, graph, reverse_graph)

        # Calculate critical path
        critical_path = self._calculate_critical_path(tasks, graph)

        # Identify bottlenecks
        bottlenecks = self._identify_bottlenecks(tasks, graph)

        # Learn from historical patterns
        optimization_suggestions = self._generate_optimizations(tasks, parallel_groups)

        return {
            "total_tasks": len(tasks),
            "dependency_depth": self._calculate_depth(graph),
            "parallel_groups": parallel_groups,
            "critical_path": critical_path,
            "bottlenecks": bottlenecks,
            "cycles": cycles,
            "optimizations": optimization_suggestions,
            "estimated_time": self._estimate_execution_time(critical_path),
        }

    def _detect_cycles(self, graph: dict[str, list[str]]) -> list[list[str]]:
        """Detect cycles in dependency graph using DFS."""
        visited = set()
        rec_stack = set()
        cycles = []

        def dfs(node: str, path: list[str]) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor, path.copy())
                elif neighbor in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(neighbor)
                    cycles.append(path[cycle_start:] + [neighbor])

            rec_stack.remove(node)

        for node in graph:
            if node not in visited:
                dfs(node, [])

        return cycles

    def _find_parallel_tasks(
        self, tasks: list[dict], graph: dict, reverse_graph: dict
    ) -> list[set[str]]:
        """Identify groups of tasks that can be executed in parallel."""
        parallel_groups = []
        processed = set()

        # Group tasks by their dependency level
        levels = defaultdict(set)

        for task in tasks:
            task_id = task["id"]
            if task_id in processed:
                continue

            level = self._get_dependency_level(task_id, reverse_graph)
            levels[level].add(task_id)
            processed.add(task_id)

        # Convert levels to parallel groups
        for level in sorted(levels.keys()):
            if len(levels[level]) > 1:
                parallel_groups.append(levels[level])

        return parallel_groups

    def _get_dependency_level(self, task_id: str, reverse_graph: dict) -> int:
        """Calculate the dependency level of a task."""
        if task_id not in reverse_graph or not reverse_graph[task_id]:
            return 0

        return 1 + max(
            self._get_dependency_level(dep, reverse_graph) for dep in reverse_graph[task_id]
        )

    def _calculate_critical_path(self, tasks: list[dict], graph: dict) -> list[str]:
        """Calculate the critical path through the task graph."""
        task_map = {t["id"]: t for t in tasks}

        # Topological sort
        in_degree = defaultdict(int)
        for node in graph:
            for neighbor in graph[node]:
                in_degree[neighbor] += 1

        queue = deque([t["id"] for t in tasks if in_degree[t["id"]] == 0])
        topo_order = []

        while queue:
            node = queue.popleft()
            topo_order.append(node)

            for neighbor in graph.get(node, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Calculate longest path (critical path)
        distances = {t["id"]: 0 for t in tasks}
        predecessors = {t["id"]: None for t in tasks}

        for node in topo_order:
            task = task_map.get(node)
            if not task:
                continue

            weight = task.get("weight", 1)

            for neighbor in graph.get(node, []):
                if distances[neighbor] < distances[node] + weight:
                    distances[neighbor] = distances[node] + weight
                    predecessors[neighbor] = node

        # Reconstruct critical path
        if not distances:
            return []

        end_node = max(distances, key=distances.get)
        path = []
        current = end_node

        while current is not None:
            path.append(current)
            current = predecessors[current]

        return list(reversed(path))

    def _calculate_depth(self, graph: dict) -> int:
        """Calculate maximum depth of the dependency graph."""
        if not graph:
            return 0

        visited = set()

        def dfs_depth(node: str) -> int:
            if node in visited:
                return 0
            visited.add(node)

            if node not in graph or not graph[node]:
                return 1

            return 1 + max(dfs_depth(child) for child in graph[node])

        return max(dfs_depth(node) for node in graph)

    def _identify_bottlenecks(self, tasks: list[dict], graph: dict) -> list[dict[str, Any]]:
        """Identify tasks that block the most other tasks."""
        bottlenecks = []
        task_map = {t["id"]: t for t in tasks}

        for task_id in graph:
            blocked_count = len(self._get_all_descendants(task_id, graph))

            if blocked_count > 3:  # Threshold for bottleneck
                bottlenecks.append(
                    {
                        "task_id": task_id,
                        "blocks": blocked_count,
                        "direct_blocks": len(graph[task_id]),
                        "status": task_map.get(task_id, {}).get("status", "unknown"),
                    }
                )

        return sorted(bottlenecks, key=lambda x: x["blocks"], reverse=True)

    def _get_all_descendants(self, node: str, graph: dict) -> set[str]:
        """Get all descendants of a node in the graph."""
        descendants = set()
        queue = deque(graph.get(node, []))

        while queue:
            current = queue.popleft()
            if current not in descendants:
                descendants.add(current)
                queue.extend(graph.get(current, []))

        return descendants

    def _estimate_execution_time(self, critical_path: list[str]) -> float:
        """Estimate execution time based on historical metrics."""
        if not critical_path:
            return 0.0

        total_time = 0.0

        for task_id in critical_path:
            # Use historical average or default estimate
            if task_id in self.metrics.get("execution_times", {}):
                avg_time = self.metrics["execution_times"][task_id].get("average", 1.0)
            else:
                avg_time = 1.0  # Default estimate in minutes

            total_time += avg_time

        return total_time

    def _generate_optimizations(self, tasks: list[dict], parallel_groups: list[set]) -> list[dict]:
        """Generate optimization suggestions based on learned patterns."""
        suggestions = []

        # Suggest parallelization opportunities
        for group in parallel_groups:
            if len(group) > 2:
                suggestions.append(
                    {
                        "type": "parallelization",
                        "tasks": list(group),
                        "impact": "high",
                        "description": f"These {len(group)} tasks can be executed in parallel",
                    }
                )

        # Suggest dependency optimizations based on learned patterns
        for task in tasks:
            task_id = task["id"]
            if task_id in self.learned_deps.get("suggested", {}):
                suggested = self.learned_deps["suggested"][task_id]
                current = set(task.get("depends_on", []))

                removable = current - set(suggested)
                if removable:
                    suggestions.append(
                        {
                            "type": "dependency_removal",
                            "task": task_id,
                            "removable_deps": list(removable),
                            "impact": "medium",
                            "description": "Historical data suggests these dependencies may be unnecessary",
                        }
                    )

        return suggestions

    def learn_from_execution(
        self,
        task_id: str,
        start_time: float,
        end_time: float,
        success: bool,
        context: dict[str, Any],
    ) -> None:
        """Learn from task execution to improve future orchestration."""
        execution_time = end_time - start_time

        # Update execution metrics
        if task_id not in self.metrics["execution_times"]:
            self.metrics["execution_times"][task_id] = {
                "samples": [],
                "average": execution_time,
                "success_rate": 1.0 if success else 0.0,
            }

        metrics = self.metrics["execution_times"][task_id]
        metrics["samples"].append(execution_time)

        # Keep only recent samples
        if len(metrics["samples"]) > 20:
            metrics["samples"] = metrics["samples"][-20:]

        metrics["average"] = sum(metrics["samples"]) / len(metrics["samples"])

        # Update success rate
        if "total_runs" not in metrics:
            metrics["total_runs"] = 0
            metrics["successful_runs"] = 0

        metrics["total_runs"] += 1
        if success:
            metrics["successful_runs"] += 1

        metrics["success_rate"] = metrics["successful_runs"] / metrics["total_runs"]

        # Learn execution patterns
        self.execution_history.append(
            {
                "task_id": task_id,
                "timestamp": datetime.now().isoformat(),
                "execution_time": execution_time,
                "success": success,
                "context": context,
            }
        )

        # Detect patterns in execution sequences
        self._analyze_execution_patterns()

        # Save updated metrics
        self._save_json(self.metrics_file, self.metrics)

    def _analyze_execution_patterns(self) -> None:
        """Analyze execution history to identify patterns."""
        if len(self.execution_history) < 10:
            return

        # Analyze task sequences
        sequences = []
        for i in range(len(self.execution_history) - 2):
            seq = [
                self.execution_history[i]["task_id"],
                self.execution_history[i + 1]["task_id"],
                self.execution_history[i + 2]["task_id"],
            ]
            sequences.append(seq)

        # Count sequence frequencies
        seq_counts = defaultdict(int)
        for seq in sequences:
            seq_key = "->".join(seq)
            seq_counts[seq_key] += 1

        # Store frequent patterns
        frequent_patterns = [
            {"sequence": seq.split("->"), "count": count}
            for seq, count in seq_counts.items()
            if count >= 3
        ]

        if frequent_patterns:
            self.patterns["task_sequences"] = frequent_patterns
            self._save_json(self.patterns_file, self.patterns)

    def suggest_next_tasks(
        self, completed_tasks: list[str], available_tasks: list[dict]
    ) -> list[tuple[str, float]]:
        """Suggest next tasks based on learned patterns and priorities.

        Returns:
            List of (task_id, confidence_score) tuples.
        """
        suggestions = []

        # Check for pattern matches
        if len(completed_tasks) >= 2:
            recent_seq = "->".join(completed_tasks[-2:])

            for pattern in self.patterns.get("task_sequences", []):
                seq = "->".join(pattern["sequence"][:2])
                if seq == recent_seq and len(pattern["sequence"]) > 2:
                    next_task = pattern["sequence"][2]

                    # Check if task is available
                    if any(t["id"] == next_task for t in available_tasks):
                        confidence = pattern["count"] / 10.0  # Normalize confidence
                        suggestions.append((next_task, min(confidence, 1.0)))

        # Add priority-based suggestions
        for task in available_tasks:
            if task["id"] not in [s[0] for s in suggestions]:
                # Calculate priority score
                priority = task.get("priority", "medium")
                priority_scores = {"critical": 1.0, "high": 0.8, "medium": 0.5, "low": 0.3}

                score = priority_scores.get(priority, 0.5)

                # Adjust based on success rate
                if task["id"] in self.metrics.get("execution_times", {}):
                    success_rate = self.metrics["execution_times"][task["id"]].get(
                        "success_rate", 1.0
                    )
                    score *= success_rate

                suggestions.append((task["id"], score))

        # Sort by confidence score
        suggestions.sort(key=lambda x: x[1], reverse=True)

        return suggestions[:5]  # Return top 5 suggestions


class AgentCoordinator:
    """Coordinates multiple agents for distributed task execution."""

    def __init__(self, orchestrator: TaskOrchestrator):
        self.orchestrator = orchestrator
        self.agents = {}
        self.agent_capabilities = {}
        self.agent_workload = defaultdict(int)

    def register_agent(self, agent_id: str, capabilities: list[str]) -> None:
        """Register an agent with its capabilities."""
        self.agents[agent_id] = {
            "status": "idle",
            "capabilities": capabilities,
            "current_task": None,
            "completed_tasks": [],
            "performance_score": 1.0,
        }

        for capability in capabilities:
            if capability not in self.agent_capabilities:
                self.agent_capabilities[capability] = []
            self.agent_capabilities[capability].append(agent_id)

    def assign_task(self, task: dict[str, Any]) -> str | None:
        """Assign a task to the most suitable available agent.

        Returns:
            Agent ID if assigned, None if no suitable agent available.
        """
        category = task.get("category", "general")

        # Find capable agents
        capable_agents = self.agent_capabilities.get(category, [])
        if not capable_agents:
            capable_agents = self.agent_capabilities.get("general", [])

        # Select best available agent
        best_agent = None
        best_score = -1

        for agent_id in capable_agents:
            agent = self.agents[agent_id]

            if agent["status"] == "idle":
                # Calculate suitability score
                score = agent["performance_score"]
                score -= self.agent_workload[agent_id] * 0.1  # Penalize high workload

                if score > best_score:
                    best_score = score
                    best_agent = agent_id

        if best_agent:
            # Assign task
            self.agents[best_agent]["status"] = "busy"
            self.agents[best_agent]["current_task"] = task["id"]
            self.agent_workload[best_agent] += 1

            logger.info(f"Assigned task {task['id']} to agent {best_agent}")
            return best_agent

        return None

    def complete_task(
        self, agent_id: str, task_id: str, success: bool, metrics: dict[str, Any]
    ) -> None:
        """Mark a task as completed by an agent."""
        if agent_id not in self.agents:
            return

        agent = self.agents[agent_id]
        agent["status"] = "idle"
        agent["current_task"] = None
        agent["completed_tasks"].append(task_id)

        # Update performance score
        if success:
            agent["performance_score"] = min(1.0, agent["performance_score"] * 1.05)
        else:
            agent["performance_score"] = max(0.1, agent["performance_score"] * 0.95)

        # Learn from execution
        self.orchestrator.learn_from_execution(
            task_id,
            metrics.get("start_time", time.time()),
            metrics.get("end_time", time.time()),
            success,
            {"agent": agent_id, **metrics},
        )

    def get_agent_status(self) -> dict[str, Any]:
        """Get current status of all agents."""
        return {
            "agents": self.agents,
            "workload_distribution": dict(self.agent_workload),
            "capability_coverage": {
                cap: len(agents) for cap, agents in self.agent_capabilities.items()
            },
        }
