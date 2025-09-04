#!/usr/bin/env python3
"""Claude Code Initialization Script - Automatically starts orchestration.

This script is automatically executed when Claude Code starts a session,
initializing the intelligent orchestration system for the Fall 2025 semester.
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dashboard.advanced_orchestrator import AdvancedOrchestrator  # noqa: E402
from dashboard.agents import AGENT_REGISTRY  # noqa: E402
from dashboard.orchestration_agent import MasterOrchestrationAgent  # noqa: E402

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ClaudeOrchestrationSystem:
    """Main orchestration system for Claude Code integration."""

    def __init__(self):
        logger.info("🚀 Initializing Claude Code Orchestration System")
        logger.info("📅 Date: August 24, 2025 - Classes begin TOMORROW!")

        # Initialize orchestrators
        self.master = MasterOrchestrationAgent()
        self.advanced = AdvancedOrchestrator()

        # Register all agents
        for agent_name, agent_class in AGENT_REGISTRY.items():
            agent = agent_class()
            self.master.coordinator.register_agent(agent_name, agent.capabilities)
            logger.info(f"✅ Registered agent: {agent_name}")

        # Load current state
        self.state = self.master.assess_current_state()

    def display_status(self):
        """Display current system status."""
        print("\n" + "=" * 60)
        print("🎯 FALL 2025 SEMESTER ORCHESTRATION STATUS")
        print("=" * 60)

        print("\n📅 Current Date: August 24, 2025")
        print("🏫 Classes Begin: August 25, 2025 (TOMORROW!)")
        print(f"⏰ Days Until Classes: {self.state['days_until_classes']}")

        if self.state["critical_issues"]:
            print(f"\n🚨 CRITICAL ISSUES ({len(self.state['critical_issues'])})")
            for issue in self.state["critical_issues"][:5]:
                print(f"  ❌ {issue}")
        else:
            print("\n✅ No critical issues detected")

        if self.state["pending_tasks"]:
            print(f"\n📋 PENDING TASKS ({len(self.state['pending_tasks'])})")
            critical_tasks = [
                t for t in self.state["pending_tasks"] if t.get("priority") == "critical"
            ]
            high_tasks = [t for t in self.state["pending_tasks"] if t.get("priority") == "high"]

            if critical_tasks:
                print(f"  🔴 Critical: {len(critical_tasks)}")
                for task in critical_tasks[:3]:
                    print(f"     - {task['title'][:60]}...")

            if high_tasks:
                print(f"  🟡 High Priority: {len(high_tasks)}")
                for task in high_tasks[:3]:
                    print(f"     - {task['title'][:60]}...")

        print(f"\n✅ COMPLETED TASKS: {len(self.state['completed_tasks'])}")

        if self.state.get("recommendations"):
            print("\n💡 RECOMMENDATIONS")
            for rec in self.state["recommendations"][:3]:
                print(f"  → {rec}")

        print("\n" + "=" * 60)
        print("🤖 ORCHESTRATION COMMANDS")
        print("=" * 60)
        print("  @orchestrate all     - Full system orchestration")
        print("  @orchestrate course  - Course-specific tasks")
        print("  @validate all        - Run all validations")
        print("  @deploy preview      - Deploy to preview")
        print("  @iframe generate     - Generate iframe codes")
        print("  @status              - Show current status")
        print("=" * 60 + "\n")

    async def execute_critical_tasks(self):
        """Execute any critical tasks automatically."""
        if self.state["critical_issues"]:
            logger.warning(f"🚨 {len(self.state['critical_issues'])} critical issues detected")
            logger.info("🔧 Initiating automatic critical task execution...")

            # Execute critical preparation
            results = self.master.execute_critical_preparation()

            if results["success"]:
                logger.info("✅ Critical preparation completed successfully")
            else:
                logger.error("❌ Critical preparation failed - manual intervention required")
                for error in results.get("errors", []):
                    logger.error(f"  - {error}")
        else:
            logger.info("✅ No critical tasks require immediate attention")

    def generate_quick_reference(self):
        """Generate quick reference card."""
        ref_card = {
            "generated": datetime.now().isoformat(),
            "semester": "Fall 2025",
            "courses": ["MATH221", "MATH251", "STAT253"],
            "critical_dates": {
                "classes_begin": "2025-08-25",
                "labor_day": "2025-09-01",
                "fall_break": "2025-11-27",
                "last_day": "2025-12-13",
                "finals": "2025-12-16 to 2025-12-20",
            },
            "orchestration_status": {
                "master_agent": "active",
                "advanced_orchestrator": "active",
                "registered_agents": len(AGENT_REGISTRY),
                "critical_issues": len(self.state.get("critical_issues", [])),
                "pending_tasks": len(self.state.get("pending_tasks", [])),
            },
            "quick_commands": {
                "validate": "make validate",
                "build_all": "make all",
                "dashboard": "make dash",
                "deploy": "@orchestrate deploy",
                "status": "@orchestrate status",
            },
            "iframe_endpoints": {
                "generator": "http://127.0.0.1:5055/embed/generator",
                "syllabus": "http://127.0.0.1:5055/embed/syllabus/{course}",
                "schedule": "http://127.0.0.1:5055/embed/schedule/{course}",
            },
        }

        # Save reference card
        ref_file = Path("dashboard/state/quick_reference.json")
        with open(ref_file, "w") as f:
            json.dump(ref_card, f, indent=2)

        logger.info(f"📋 Quick reference saved to {ref_file}")

        return ref_card

    async def start_monitoring(self):
        """Start continuous monitoring loop."""
        logger.info("👁️ Starting continuous orchestration monitoring...")

        while True:
            try:
                # Reassess state every 5 minutes
                await asyncio.sleep(300)

                self.state = self.master.assess_current_state()

                # Check for new critical issues
                if self.state["critical_issues"]:
                    logger.warning(
                        f"⚠️ New critical issues detected: {len(self.state['critical_issues'])}"
                    )
                    await self.execute_critical_tasks()

                # Log status
                logger.info(
                    f"📊 Status: {len(self.state['completed_tasks'])} completed, "
                    f"{len(self.state['pending_tasks'])} pending"
                )

            except KeyboardInterrupt:
                logger.info("🛑 Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Monitoring error: {e}")
                await asyncio.sleep(30)


async def main():
    """Main entry point for Claude orchestration."""
    print("\n🤖 CLAUDE CODE INTELLIGENT ORCHESTRATION SYSTEM")
    print("=" * 60)
    print("Initializing Fall 2025 Semester Management...")
    print("=" * 60)

    # Initialize system
    system = ClaudeOrchestrationSystem()

    # Display status
    system.display_status()

    # Generate quick reference
    system.generate_quick_reference()

    # Execute critical tasks if needed
    await system.execute_critical_tasks()

    # Inform user
    print("\n✅ Orchestration system is now active and monitoring")
    print("💡 Use @orchestrate commands to interact with the system")
    print("📊 Dashboard available at http://127.0.0.1:5055")
    print("🔄 System will continuously monitor and optimize task execution\n")

    # Start monitoring in background
    # Note: In actual Claude Code integration, this would run as a background task
    # For now, we just set it up but don't block
    _monitor_task = asyncio.create_task(system.start_monitoring())

    # Return system for Claude to use
    return system


# This will be called when Claude Code starts
if __name__ == "__main__":
    # Run initialization
    system = asyncio.run(main())

    # Make system available globally for Claude
    import builtins

    builtins.orchestration = system
    builtins.orchestrator = system.master
    builtins.advanced_orchestrator = system.advanced

    print("🎯 Orchestration system loaded into global scope")
    print("   Access via: orchestration, orchestrator, advanced_orchestrator")
