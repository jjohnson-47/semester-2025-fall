#!/usr/bin/env python3
"""Master Orchestration Agent for Fall 2025 Semester Management.

This is the primary orchestration agent that coordinates all semester preparation tasks,
manages agent teams, and ensures everything is ready for the Fall 2025 semester.
It integrates with the task management system and provides intelligent automation.

CRITICAL: This agent is designed for immediate production use (August 24, 2025).
"""

import asyncio
import json
import logging
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dashboard.orchestrator import AgentCoordinator, TaskOrchestrator

logger = logging.getLogger(__name__)


class MasterOrchestrationAgent:
    """Master agent that orchestrates all semester preparation activities."""

    def __init__(self):
        self.state_dir = Path("dashboard/state")
        self.state_dir.mkdir(exist_ok=True)

        # Initialize core components
        self.orchestrator = TaskOrchestrator(self.state_dir)
        self.coordinator = AgentCoordinator(self.orchestrator)

        # Agent registry with specialized capabilities
        self.agent_registry = {
            "course-content": {
                "capabilities": ["content", "syllabi", "schedules", "materials"],
                "commands": ["make syllabi", "make schedules", "make weekly"],
                "priority": "critical",
            },
            "qa-validator": {
                "capabilities": ["validation", "quality", "testing"],
                "commands": ["make validate", "make test"],
                "priority": "high",
            },
            "calendar-sync": {
                "capabilities": ["calendar", "dates", "synchronization"],
                "commands": ["make calendar", "python scripts/utils/semester_calendar.py"],
                "priority": "high",
            },
            "blackboard-integrator": {
                "capabilities": ["blackboard", "lti", "integration"],
                "commands": ["make packages"],
                "priority": "medium",
            },
            "deployment-manager": {
                "capabilities": ["deployment", "hosting", "publishing"],
                "commands": ["make site", "make deploy"],
                "priority": "medium",
            },
        }

        # Register all agents
        for agent_id, config in self.agent_registry.items():
            self.coordinator.register_agent(agent_id, config["capabilities"])

        # Semester timeline (critical dates for Fall 2025)
        self.critical_dates = {
            "2025-08-24": "Today - Final preparation",
            "2025-08-25": "Classes begin - FIRST DAY",
            "2025-09-01": "Labor Day (no classes)",
            "2025-10-11": "Fall Break begins",
            "2025-11-27": "Thanksgiving Break begins",
            "2025-12-13": "Last day of classes",
            "2025-12-16": "Finals week begins",
        }

        # Current status
        self.execution_log = []
        self.current_phase = "critical-preparation"  # We're in critical prep phase

    def assess_current_state(self) -> dict[str, Any]:
        """Assess the current state of semester preparation."""
        assessment = {
            "timestamp": datetime.now().isoformat(),
            "days_until_classes": 1,  # Classes start Aug 25
            "critical_issues": [],
            "pending_tasks": [],
            "completed_tasks": [],
            "recommendations": [],
        }

        # Load current tasks
        tasks_file = self.state_dir / "tasks.json"
        if tasks_file.exists():
            with open(tasks_file) as f:
                data = json.load(f)
                tasks = data.get("tasks", [])

                # Categorize tasks by status
                for task in tasks:
                    status = task.get("status", "unknown")
                    if status == "done":
                        assessment["completed_tasks"].append(task["id"])
                    elif status in ["todo", "doing", "blocked"]:
                        assessment["pending_tasks"].append(
                            {
                                "id": task["id"],
                                "title": task.get("title", ""),
                                "status": status,
                                "priority": task.get("priority", "medium"),
                                "course": task.get("course", "General"),
                            }
                        )

                        # Check for critical issues
                        if task.get("priority") == "critical" and status != "done":
                            assessment["critical_issues"].append(
                                f"Critical task not complete: {task['title']}"
                            )

        # Check build artifacts
        build_checks = {
            "syllabi": Path("build/syllabi").exists(),
            "schedules": Path("build/schedules").exists(),
            "weekly": Path("build/weekly").exists(),
            "blackboard": Path("build/blackboard").exists(),
        }

        for artifact, exists in build_checks.items():
            if not exists:
                assessment["critical_issues"].append(f"Missing build artifact: {artifact}")
                assessment["recommendations"].append(
                    f"Run 'make {artifact}' to generate {artifact}"
                )

        # Analyze task dependencies
        if tasks:
            analysis = self.orchestrator.analyze_task_graph(tasks)
            assessment["orchestration_analysis"] = analysis

            # Add optimization recommendations
            for opt in analysis.get("optimizations", []):
                if opt["impact"] == "high":
                    assessment["recommendations"].append(
                        f"High-impact optimization: {opt['description']}"
                    )

        return assessment

    def execute_critical_preparation(self) -> dict[str, Any]:
        """Execute critical preparation tasks for semester start."""
        results = {
            "phase": "critical-preparation",
            "started": datetime.now().isoformat(),
            "actions": [],
            "errors": [],
            "warnings": [],
        }

        # Priority order of operations
        critical_steps = [
            {
                "name": "Validate All JSON",
                "command": "make validate",
                "agent": "qa-validator",
                "required": True,
            },
            {
                "name": "Generate Calendar",
                "command": "make calendar",
                "agent": "calendar-sync",
                "required": True,
            },
            {
                "name": "Build Syllabi",
                "command": "make syllabi",
                "agent": "course-content",
                "required": True,
            },
            {
                "name": "Build Schedules",
                "command": "make schedules",
                "agent": "course-content",
                "required": True,
            },
            {
                "name": "Generate Weekly Folders",
                "command": "make weekly",
                "agent": "course-content",
                "required": False,
            },
            {
                "name": "Create Blackboard Packages",
                "command": "make packages",
                "agent": "blackboard-integrator",
                "required": False,
            },
        ]

        for step in critical_steps:
            action_result = {
                "step": step["name"],
                "agent": step["agent"],
                "status": "pending",
                "output": "",
                "duration": 0,
            }

            start_time = time.time()

            try:
                # Execute command
                result = subprocess.run(
                    step["command"],
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5 minute timeout
                )

                action_result["duration"] = time.time() - start_time
                action_result["output"] = result.stdout

                if result.returncode == 0:
                    action_result["status"] = "success"
                    logger.info(f"Successfully completed: {step['name']}")
                else:
                    action_result["status"] = "failed"
                    action_result["error"] = result.stderr

                    if step["required"]:
                        results["errors"].append(f"Critical step failed: {step['name']}")
                    else:
                        results["warnings"].append(f"Optional step failed: {step['name']}")

                    logger.error(f"Failed: {step['name']} - {result.stderr}")

            except subprocess.TimeoutExpired:
                action_result["status"] = "timeout"
                results["errors"].append(f"Step timed out: {step['name']}")

            except Exception as e:
                action_result["status"] = "error"
                action_result["error"] = str(e)
                results["errors"].append(f"Exception in {step['name']}: {e}")

            results["actions"].append(action_result)

            # Learn from execution
            self.orchestrator.learn_from_execution(
                step["name"],
                start_time,
                time.time(),
                action_result["status"] == "success",
                {"agent": step["agent"], "command": step["command"]},
            )

        results["completed"] = datetime.now().isoformat()
        results["success"] = len(results["errors"]) == 0

        return results

    def generate_deployment_checklist(self) -> dict[str, list[str]]:
        """Generate comprehensive deployment checklist for each course."""
        checklist = {"MATH221": [], "MATH251": [], "STAT253": [], "General": []}

        # Common items for all courses
        common_items = [
            "✓ Syllabus generated and reviewed",
            "✓ Schedule aligned with academic calendar",
            "✓ Office hours confirmed",
            "✓ Grading rubrics finalized",
            "✓ Blackboard course shell ready",
            "✓ Welcome announcement prepared",
            "✓ First week materials uploaded",
            "✓ Assignment due dates verified",
            "✓ LTI tools configured",
            "✓ Gradebook categories set up",
        ]

        # Course-specific items
        specific_items = {
            "MATH221": [
                "✓ MyOpenMath course copied",
                "✓ Friday deadline pattern confirmed",
                "✓ Discussion board topics created",
                "✓ Weekly quizzes scheduled",
            ],
            "MATH251": [
                "✓ Edfinity assignments imported",
                "✓ Written problems template ready",
                "✓ Exam schedule posted",
                "✓ Calculator policy clarified",
            ],
            "STAT253": [
                "✓ Pearson MyLab access verified",
                "✓ R/RStudio instructions posted",
                "✓ Data files uploaded",
                "✓ Project guidelines published",
            ],
        }

        # Build complete checklists
        for course in ["MATH221", "MATH251", "STAT253"]:
            checklist[course] = common_items + specific_items.get(course, [])

        # General administrative items
        checklist["General"] = [
            "✓ All rosters downloaded",
            "✓ Attendance tracking system ready",
            "✓ Emergency procedures reviewed",
            "✓ Department meeting attended",
            "✓ IT support contact confirmed",
            "✓ Backup plans prepared",
            "✓ Student accommodations reviewed",
            "✓ Academic integrity policy posted",
        ]

        return checklist

    def create_iframe_deployment_package(self) -> dict[str, Any]:
        """Create deployment package with iframe codes for Blackboard Ultra."""
        package = {
            "created": datetime.now().isoformat(),
            "base_url": "http://127.0.0.1:5055",  # Update with production URL
            "courses": {},
        }

        for course in ["MATH221", "MATH251", "STAT253"]:
            package["courses"][course] = {
                "syllabus_iframe": f"""<iframe src="{package['base_url']}/embed/syllabus/{course}"
width="100%" height="800" frameborder="0"
style="border: 1px solid #ddd; border-radius: 4px;"
title="{course} Syllabus"></iframe>""",
                "schedule_iframe": f"""<iframe src="{package['base_url']}/embed/schedule/{course}"
width="100%" height="600" frameborder="0"
style="border: 1px solid #ddd; border-radius: 4px;"
title="{course} Schedule"></iframe>""",
                "instructions": [
                    "1. Log into Blackboard Ultra",
                    f"2. Navigate to your {course} course",
                    "3. Create or edit a content area",
                    "4. Click the HTML editor button (</>)",
                    "5. Paste the iframe code",
                    "6. Save the content",
                    "7. The syllabus/schedule will appear embedded",
                ],
            }

        # Save deployment package
        deploy_file = self.state_dir / "iframe_deployment.json"
        with open(deploy_file, "w") as f:
            json.dump(package, f, indent=2)

        return package

    async def run_continuous_orchestration(self):
        """Run continuous orchestration loop."""
        logger.info("Starting continuous orchestration for Fall 2025 semester")

        while True:
            try:
                # Assess current state
                state = self.assess_current_state()

                # Check for critical issues
                if state["critical_issues"]:
                    logger.warning(f"Critical issues detected: {state['critical_issues']}")

                    # Attempt automatic resolution
                    if self.current_phase == "critical-preparation":
                        logger.info("Executing critical preparation sequence...")
                        prep_results = self.execute_critical_preparation()

                        if prep_results["success"]:
                            logger.info("Critical preparation completed successfully")
                            self.current_phase = "monitoring"
                        else:
                            logger.error(f"Preparation failed: {prep_results['errors']}")

                # Process pending tasks
                if state["pending_tasks"]:
                    # Sort by priority
                    high_priority = [
                        t for t in state["pending_tasks"] if t["priority"] in ["critical", "high"]
                    ]

                    for task in high_priority[:5]:  # Process top 5
                        # Find suitable agent
                        agent_id = self.coordinator.assign_task(task)
                        if agent_id:
                            logger.info(f"Assigned task {task['id']} to {agent_id}")

                # Generate status report
                self.generate_status_report(state)

                # Sleep before next iteration
                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(f"Orchestration error: {e}")
                await asyncio.sleep(30)  # Shorter sleep on error

    def generate_status_report(self, state: dict[str, Any]) -> None:
        """Generate and save status report."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "phase": self.current_phase,
            "days_until_classes": state["days_until_classes"],
            "completion_percentage": 0,
            "status": "preparing",
        }

        # Calculate completion percentage
        total_tasks = len(state["completed_tasks"]) + len(state["pending_tasks"])
        if total_tasks > 0:
            report["completion_percentage"] = len(state["completed_tasks"]) / total_tasks * 100

        # Determine overall status
        if report["completion_percentage"] >= 95:
            report["status"] = "ready"
        elif report["completion_percentage"] >= 80:
            report["status"] = "nearly_ready"
        elif state["critical_issues"]:
            report["status"] = "critical"

        # Add recommendations
        report["next_actions"] = state.get("recommendations", [])[:3]

        # Save report
        report_file = self.state_dir / "orchestration_status.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        # Log summary
        logger.info(
            f"Status: {report['status']} - "
            f"{report['completion_percentage']:.1f}% complete - "
            f"{state['days_until_classes']} days until classes"
        )


def main():
    """Main entry point for the orchestration agent."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    agent = MasterOrchestrationAgent()

    # Initial assessment
    logger.info("=== FALL 2025 SEMESTER ORCHESTRATION AGENT ===")
    logger.info("Current date: August 24, 2025")
    logger.info("Classes begin: August 25, 2025 (TOMORROW)")

    state = agent.assess_current_state()

    if state["critical_issues"]:
        logger.warning("CRITICAL ISSUES DETECTED - Initiating emergency preparation")
        prep_results = agent.execute_critical_preparation()

        if prep_results["success"]:
            logger.info("✓ Emergency preparation completed successfully")
        else:
            logger.error("✗ Emergency preparation failed - manual intervention required")
            for error in prep_results["errors"]:
                logger.error(f"  - {error}")

    # Generate deployment materials
    logger.info("Generating iframe deployment package...")
    _deployment = agent.create_iframe_deployment_package()
    logger.info(f"✓ Deployment package created: {agent.state_dir}/iframe_deployment.json")

    # Generate checklist
    checklist = agent.generate_deployment_checklist()
    checklist_file = agent.state_dir / "deployment_checklist.json"
    with open(checklist_file, "w") as f:
        json.dump(checklist, f, indent=2)
    logger.info(f"✓ Deployment checklist created: {checklist_file}")

    # Start continuous orchestration
    logger.info("Starting continuous orchestration loop...")
    try:
        asyncio.run(agent.run_continuous_orchestration())
    except KeyboardInterrupt:
        logger.info("Orchestration stopped by user")


if __name__ == "__main__":
    main()
