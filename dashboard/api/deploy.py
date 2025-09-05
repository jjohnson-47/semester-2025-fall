#!/usr/bin/env python3
"""Deployment API for dashboard Deploy button.

Handles the complete deployment pipeline from build to verification,
integrating with the v2 templating architecture.
"""

import asyncio
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from flask import Blueprint, jsonify, request

# Create blueprint for deployment routes
deploy_bp = Blueprint("deploy", __name__, url_prefix="/api/deploy")

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
WORKER_DIR = PROJECT_ROOT.parent / "jeffsthings-courses"
SITE_DIR = PROJECT_ROOT / "site"
LOG_DIR = PROJECT_ROOT / "logs"

# Ensure log directory exists
LOG_DIR.mkdir(exist_ok=True)


class DeploymentManager:
    """Manages the deployment pipeline for course content."""

    def __init__(self):
        self.current_deployment: dict[str, Any] | None = None
        self.deployment_log: list[dict[str, Any]] = []
        self.is_deploying: bool = False

    async def run_command(
        self, cmd: str, cwd: Path | None = None, env: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Run a shell command asynchronously and capture output."""
        self.log(f"Running: {cmd}")

        # Merge environment variables
        cmd_env = os.environ.copy()
        if env:
            cmd_env.update(env)

        try:
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(cwd) if cwd else None,
                env=cmd_env,
            )

            stdout, stderr = await process.communicate()

            result = {
                "command": cmd,
                "returncode": process.returncode,
                "stdout": stdout.decode("utf-8"),
                "stderr": stderr.decode("utf-8"),
                "success": process.returncode == 0,
            }

            if not result["success"]:
                self.log(f"Command failed: {stderr.decode('utf-8')}", level="error")
            else:
                self.log("Command succeeded", level="success")

            return result

        except Exception as e:
            self.log(f"Command exception: {e!s}", level="error")
            return {
                "command": cmd,
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
                "success": False,
            }

    def log(self, message: str, level: str = "info"):
        """Add a message to the deployment log."""
        entry = {"timestamp": datetime.now().isoformat(), "level": level, "message": message}
        self.deployment_log.append(entry)

        # Also write to file
        log_file = LOG_DIR / f"deployment_{datetime.now().strftime('%Y%m%d')}.log"
        with open(log_file, "a") as f:
            f.write(f"[{entry['timestamp']}] [{entry['level'].upper()}] {entry['message']}\n")

    async def build_site(self) -> dict[str, Any]:
        """Build the site with v2 templating."""
        self.log("Starting site build with v2 mode")

        result = await self.run_command(
            "make build-site", cwd=PROJECT_ROOT, env={"BUILD_MODE": "v2", "ENV": "production"}
        )

        # Verify site was built
        if result["success"]:
            manifest_path = SITE_DIR / "manifest.json"
            if manifest_path.exists():
                self.log("Site build completed successfully", level="success")
            else:
                result["success"] = False
                result["stderr"] = "Site build completed but manifest.json not found"
                self.log("Site build failed: manifest missing", level="error")

        return result

    async def sync_content(self) -> dict[str, Any]:
        """Sync content to jeffsthings-courses."""
        self.log("Syncing content to worker directory")

        if not WORKER_DIR.exists():
            self.log(f"Worker directory not found: {WORKER_DIR}", level="error")
            return {"success": False, "stderr": f"Worker directory not found: {WORKER_DIR}"}

        result = await self.run_command("pnpm sync", cwd=WORKER_DIR)

        if result["success"]:
            self.log("Content sync completed", level="success")

        return result

    async def deploy_worker(self) -> dict[str, Any]:
        """Deploy to Cloudflare Workers."""
        self.log("Deploying to Cloudflare Workers")

        result = await self.run_command("pnpm deploy", cwd=WORKER_DIR)

        if result["success"]:
            # Extract deployment URL from output
            output = result["stdout"]
            if "courses.jeffsthings.com" in output:
                self.log("Worker deployment successful", level="success")
            else:
                self.log("Worker deployed but URL not confirmed", level="warning")

        return result

    async def verify_deployment(self) -> dict[str, Any]:
        """Verify the deployment is working."""
        self.log("Verifying deployment")

        result = await self.run_command("pnpm verify", cwd=WORKER_DIR)

        if result["success"]:
            self.log("Deployment verification passed", level="success")
        else:
            self.log("Deployment verification failed", level="warning")

        return result

    async def execute_full_deployment(self) -> dict[str, Any]:
        """Execute the complete deployment pipeline."""
        if self.is_deploying:
            return {"status": "error", "message": "Deployment already in progress"}

        self.is_deploying = True
        self.deployment_log = []
        start_time = datetime.now()

        self.log("Starting full deployment pipeline")

        deployment_result = {
            "status": "success",
            "start_time": start_time.isoformat(),
            "steps": {},
            "production_url": "https://courses.jeffsthings.com",
        }

        try:
            # Step 1: Build site with v2 mode
            self.log("Step 1/4: Building site", level="info")
            build_result = await self.build_site()
            deployment_result["steps"]["build"] = {
                "success": build_result["success"],
                "duration": (datetime.now() - start_time).total_seconds(),
            }

            if not build_result["success"]:
                raise Exception(f"Build failed: {build_result.get('stderr', 'Unknown error')}")

            # Step 2: Sync content
            self.log("Step 2/4: Syncing content", level="info")
            sync_start = datetime.now()
            sync_result = await self.sync_content()
            deployment_result["steps"]["sync"] = {
                "success": sync_result["success"],
                "duration": (datetime.now() - sync_start).total_seconds(),
            }

            if not sync_result["success"]:
                raise Exception(f"Sync failed: {sync_result.get('stderr', 'Unknown error')}")

            # Step 3: Deploy to Cloudflare
            self.log("Step 3/4: Deploying to Cloudflare", level="info")
            deploy_start = datetime.now()
            deploy_result = await self.deploy_worker()
            deployment_result["steps"]["deploy"] = {
                "success": deploy_result["success"],
                "duration": (datetime.now() - deploy_start).total_seconds(),
            }

            if not deploy_result["success"]:
                raise Exception(f"Deploy failed: {deploy_result.get('stderr', 'Unknown error')}")

            # Step 4: Verify deployment
            self.log("Step 4/4: Verifying deployment", level="info")
            verify_start = datetime.now()
            verify_result = await self.verify_deployment()
            deployment_result["steps"]["verify"] = {
                "success": verify_result["success"],
                "duration": (datetime.now() - verify_start).total_seconds(),
            }

            # Calculate total duration
            deployment_result["end_time"] = datetime.now().isoformat()
            deployment_result["total_duration"] = (datetime.now() - start_time).total_seconds()

            # Set final status
            if all(step["success"] for step in deployment_result["steps"].values()):
                self.log("Deployment completed successfully!", level="success")
                deployment_result["status"] = "success"
            else:
                self.log("Deployment completed with warnings", level="warning")
                deployment_result["status"] = "warning"

        except Exception as e:
            self.log(f"Deployment failed: {e!s}", level="error")
            deployment_result["status"] = "error"
            deployment_result["error"] = str(e)
            deployment_result["end_time"] = datetime.now().isoformat()
            deployment_result["total_duration"] = (datetime.now() - start_time).total_seconds()

        finally:
            self.is_deploying = False
            deployment_result["log"] = self.deployment_log[-20:]  # Last 20 log entries
            self.current_deployment = deployment_result

        return deployment_result


# Create global deployment manager instance
deployment_manager = DeploymentManager()


# API Routes
@deploy_bp.route("/trigger", methods=["POST"])
async def trigger_deployment():
    """Trigger a full deployment."""
    result = await deployment_manager.execute_full_deployment()
    return jsonify(result)


@deploy_bp.route("/status", methods=["GET"])
def get_deployment_status():
    """Get current deployment status."""
    if deployment_manager.is_deploying:
        return jsonify(
            {
                "status": "deploying",
                "message": "Deployment in progress",
                "log": deployment_manager.deployment_log[-10:],
            }
        )
    elif deployment_manager.current_deployment:
        return jsonify({"status": "idle", "last_deployment": deployment_manager.current_deployment})
    else:
        return jsonify({"status": "idle", "message": "No deployments executed yet"})


@deploy_bp.route("/logs", methods=["GET"])
def get_deployment_logs():
    """Get deployment logs."""
    limit = request.args.get("limit", 50, type=int)
    return jsonify(
        {
            "logs": deployment_manager.deployment_log[-limit:],
            "total_entries": len(deployment_manager.deployment_log),
        }
    )


@deploy_bp.route("/verify", methods=["GET"])
async def verify_current_deployment():
    """Verify current deployment without deploying."""
    result = await deployment_manager.verify_deployment()
    return jsonify(
        {
            "verified": result["success"],
            "output": result.get("stdout", ""),
            "errors": result.get("stderr", ""),
        }
    )


# Export for use in main app
def register_deploy_routes(app):
    """Register deployment routes with the main Flask app."""
    app.register_blueprint(deploy_bp)
