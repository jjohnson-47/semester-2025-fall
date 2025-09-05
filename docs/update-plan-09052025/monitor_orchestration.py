#!/usr/bin/env python3
"""
Orchestration Tracker Monitor
Real-time monitoring dashboard for multiagent orchestration.
Save as: monitor_orchestration.py
Usage: python3 monitor_orchestration.py [--web]
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# Try to import optional dependencies
try:
    from flask import Flask, jsonify, render_template_string

    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False


class OrchestrationMonitor:
    """Monitor and report on orchestration progress."""

    def __init__(self, tracker_file: str = ".orchestration/tracker.json"):
        self.tracker_file = Path(tracker_file)
        self.last_update = None
        self.data = {}

    def read_tracker(self) -> dict[str, Any]:
        """Read the tracker file safely."""
        try:
            if self.tracker_file.exists():
                with open(self.tracker_file) as f:
                    return json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            print(f"Error reading tracker: {e}")
        return {}

    def get_agent_status_icon(self, status: str) -> str:
        """Get status icon for agent."""
        icons = {"completed": "✓", "failed": "✗", "running": "→", "created": "○", "removed": "⊘"}
        return icons.get(status, "?")

    def get_lane_status_icon(self, status: str) -> str:
        """Get status icon for lane."""
        icons = {"completed": "✓", "failed": "✗", "running": "→", "pending": "○", "blocked": "⊗"}
        return icons.get(status, "?")

    def format_timestamp(self, timestamp: str) -> str:
        """Format ISO timestamp to readable format."""
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            return dt.strftime("%H:%M:%S")
        except (ValueError, AttributeError):
            return timestamp

    def print_status(self):
        """Print formatted status to console."""
        os.system("clear" if os.name != "nt" else "cls")

        data = self.data
        if not data:
            print("No tracker data available")
            return

        # Header
        print(f"{'=' * 60}")
        print(f"ORCHESTRATION STATUS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'=' * 60}")

        # Overall status
        phase = data.get("phase", 0)
        status = data.get("status", "unknown")
        print(f"\nPhase: {phase} | Status: {status}")
        if "updated_at" in data:
            print(f"Last Update: {self.format_timestamp(data['updated_at'])}")

        # Progress bar for phases
        phases = ["Init", "Probes", "Planning", "Execution", "Complete"]
        progress = "["
        for i, _ in enumerate(phases):
            if i < phase:
                progress += "■"
            elif i == phase:
                progress += "▶"
            else:
                progress += "□"
        progress += "]"
        print(f"Progress: {progress} {phases[min(phase, len(phases) - 1)]}")

        # Agents section
        agents = data.get("agents", {})
        if agents:
            print(f"\n{'AGENTS':^20} {'STATUS':^12} {'LANE':^20} {'WORKTREE':^30}")
            print("-" * 82)
            for agent_id, agent in agents.items():
                icon = self.get_agent_status_icon(agent["status"])
                worktree = agent.get("worktree", "").split("/")[-2:]
                worktree_short = "/".join(worktree) if worktree else "N/A"
                print(
                    f"{icon} {agent_id[:18]:<18} {agent['status']:<12} {agent.get('lane', 'N/A')[:18]:<20} {worktree_short:<30}"
                )

        # Lanes section
        lanes = data.get("lanes", {})
        if lanes:
            print(
                f"\n{'LANES':^20} {'STATUS':^12} {'PRIORITY':^10} {'RESULTS':^10} {'PROGRESS':^30}"
            )
            print("-" * 82)

            # Sort lanes by priority
            sorted_lanes = sorted(
                lanes.items(),
                key=lambda x: {"high": 0, "medium": 1, "low": 2}.get(
                    x[1].get("priority", "low"), 3
                ),
            )

            for lane_id, lane in sorted_lanes:
                icon = self.get_lane_status_icon(lane["status"])
                priority = lane.get("priority", "normal")
                results_count = len(lane.get("results", []))
                progress = lane.get("progress", "")[:28]

                # Color coding for priority
                if priority == "high":
                    priority_str = "HIGH"
                elif priority == "medium":
                    priority_str = "MED"
                else:
                    priority_str = "LOW"

                print(
                    f"{icon} {lane_id[:18]:<18} {lane['status']:<12} {priority_str:<10} {results_count:<10} {progress:<30}"
                )

                # Show tasks if running
                if lane["status"] == "running" and "tasks" in lane:
                    for task in lane.get("tasks", [])[:3]:
                        print(f"     └─ {task[:70]}")

        # Statistics
        print(f"\n{'STATISTICS':^60}")
        print("-" * 60)

        total_agents = len(agents)
        active_agents = sum(1 for a in agents.values() if a["status"] == "running")
        completed_agents = sum(1 for a in agents.values() if a["status"] == "completed")
        failed_agents = sum(1 for a in agents.values() if a["status"] == "failed")

        total_lanes = len(lanes)
        completed_lanes = sum(1 for lane in lanes.values() if lane["status"] == "completed")
        failed_lanes = sum(1 for lane in lanes.values() if lane["status"] == "failed")
        running_lanes = sum(1 for lane in lanes.values() if lane["status"] == "running")

        print(
            f"Agents:  Total: {total_agents} | Active: {active_agents} | Done: {completed_agents} | Failed: {failed_agents}"
        )
        print(
            f"Lanes:   Total: {total_lanes} | Running: {running_lanes} | Done: {completed_lanes} | Failed: {failed_lanes}"
        )

        # Calculate completion percentage
        if total_lanes > 0:
            completion = (completed_lanes / total_lanes) * 100
            print(f"Overall Completion: {completion:.1f}%")

            # Progress bar
            bar_length = 40
            filled = int(bar_length * completion / 100)
            bar = "█" * filled + "░" * (bar_length - filled)
            print(f"Progress: [{bar}] {completion:.1f}%")

        # Warnings or errors
        if failed_agents > 0 or failed_lanes > 0:
            print("\n⚠️  WARNINGS:")
            if failed_agents > 0:
                print(f"   - {failed_agents} agent(s) failed")
            if failed_lanes > 0:
                print(f"   - {failed_lanes} lane(s) failed")
                for lane_id, lane in lanes.items():
                    if lane["status"] == "failed":
                        print(f"     • {lane_id}")

    def monitor_console(self, refresh_rate: int = 2):
        """Monitor in console with auto-refresh."""
        print("Starting orchestration monitor... (Press Ctrl+C to exit)")

        try:
            while True:
                self.data = self.read_tracker()
                current_update = self.data.get("updated_at")

                if current_update != self.last_update:
                    self.print_status()
                    self.last_update = current_update

                time.sleep(refresh_rate)

        except KeyboardInterrupt:
            print("\n\nMonitoring stopped.")
            sys.exit(0)

    def get_json_status(self) -> dict:
        """Get status as JSON for web interface."""
        data = self.read_tracker()

        # Calculate statistics
        agents = data.get("agents", {})
        lanes = data.get("lanes", {})

        stats = {
            "agents_total": len(agents),
            "agents_active": sum(1 for a in agents.values() if a["status"] == "running"),
            "agents_completed": sum(1 for a in agents.values() if a["status"] == "completed"),
            "agents_failed": sum(1 for a in agents.values() if a["status"] == "failed"),
            "lanes_total": len(lanes),
            "lanes_running": sum(1 for lane in lanes.values() if lane["status"] == "running"),
            "lanes_completed": sum(1 for lane in lanes.values() if lane["status"] == "completed"),
            "lanes_failed": sum(1 for lane in lanes.values() if lane["status"] == "failed"),
            "completion_percentage": 0,
        }

        if stats["lanes_total"] > 0:
            stats["completion_percentage"] = round(
                (stats["lanes_completed"] / stats["lanes_total"]) * 100, 1
            )

        return {"data": data, "stats": stats, "timestamp": datetime.now().isoformat()}

    def run_web_server(self, host: str = "127.0.0.1", port: int = 5555):
        """Run web-based monitoring dashboard."""
        if not HAS_FLASK:
            print("Flask not installed. Install with: pip install flask")
            return

        app = Flask(__name__)
        monitor = self

        HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Orchestration Monitor</title>
    <meta charset="utf-8">
    <meta http-equiv="refresh" content="2">
    <style>
        body { font-family: monospace; background: #1e1e1e; color: #d4d4d4; padding: 20px; }
        .header { background: #2d2d2d; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
        .section { background: #2d2d2d; padding: 15px; border-radius: 5px; margin-bottom: 15px; }
        h1 { color: #569cd6; margin: 0; }
        h2 { color: #4ec9b0; border-bottom: 1px solid #3c3c3c; padding-bottom: 5px; }
        .status-completed { color: #4ec9b0; }
        .status-failed { color: #f44747; }
        .status-running { color: #dcdcaa; }
        .status-pending { color: #808080; }
        .progress-bar { background: #3c3c3c; height: 30px; border-radius: 5px; overflow: hidden; }
        .progress-fill { background: linear-gradient(90deg, #4ec9b0, #569cd6); height: 100%; transition: width 0.3s; }
        table { width: 100%; border-collapse: collapse; }
        th { text-align: left; padding: 8px; border-bottom: 2px solid #3c3c3c; color: #569cd6; }
        td { padding: 8px; border-bottom: 1px solid #3c3c3c; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; }
        .stat-box { background: #3c3c3c; padding: 10px; border-radius: 5px; text-align: center; }
        .stat-value { font-size: 24px; font-weight: bold; color: #569cd6; }
        .stat-label { font-size: 12px; color: #808080; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 Orchestration Monitor</h1>
        <p>Last refresh: {{ timestamp }}</p>
    </div>
    
    <div class="section">
        <h2>Overview</h2>
        <p>Phase: <strong>{{ data.phase }}</strong> | Status: <strong class="status-{{ data.status }}">{{ data.status }}</strong></p>
        <div class="progress-bar">
            <div class="progress-fill" style="width: {{ stats.completion_percentage }}%"></div>
        </div>
        <p style="text-align: center;">{{ stats.completion_percentage }}% Complete</p>
    </div>
    
    <div class="section">
        <h2>Statistics</h2>
        <div class="stats-grid">
            <div class="stat-box">
                <div class="stat-value">{{ stats.agents_total }}</div>
                <div class="stat-label">Total Agents</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{{ stats.agents_active }}</div>
                <div class="stat-label">Active</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{{ stats.agents_completed }}</div>
                <div class="stat-label">Completed</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{{ stats.lanes_total }}</div>
                <div class="stat-label">Total Lanes</div>
            </div>
        </div>
    </div>
    
    <div class="section">
        <h2>Active Lanes</h2>
        <table>
            <tr>
                <th>Lane ID</th>
                <th>Status</th>
                <th>Priority</th>
                <th>Agent</th>
            </tr>
            {% for lane_id, lane in data.lanes.items() %}
            <tr>
                <td>{{ lane_id }}</td>
                <td class="status-{{ lane.status }}">{{ lane.status }}</td>
                <td>{{ lane.priority|default('normal') }}</td>
                <td>
                    {% for agent_id, agent in data.agents.items() %}
                        {% if agent.lane == lane_id %}
                            {{ agent_id }}
                        {% endif %}
                    {% endfor %}
                </td>
            </tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
        """

        @app.route("/")
        def dashboard():
            status = monitor.get_json_status()
            return render_template_string(HTML_TEMPLATE, **status)

        @app.route("/api/status")
        def api_status():
            return jsonify(monitor.get_json_status())

        print(f"Starting web monitor at http://{host}:{port}")
        app.run(host=host, port=port, debug=False)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Monitor orchestration progress")
    parser.add_argument(
        "--tracker", default=".orchestration/tracker.json", help="Path to tracker file"
    )
    parser.add_argument("--web", action="store_true", help="Run web-based monitor")
    parser.add_argument("--port", type=int, default=5555, help="Web server port (default: 5555)")
    parser.add_argument(
        "--refresh", type=int, default=2, help="Refresh rate in seconds (default: 2)"
    )

    args = parser.parse_args()

    monitor = OrchestrationMonitor(args.tracker)

    if args.web:
        monitor.run_web_server(port=args.port)
    else:
        monitor.monitor_console(refresh_rate=args.refresh)


if __name__ == "__main__":
    main()
