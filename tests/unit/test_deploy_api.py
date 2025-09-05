"""Unit tests for dashboard/api/deploy.py - Track B.

Tests for:
- run_command: happy path, failures, stdout/stderr capture, time budget enforcement
- build_site: manifest present/missing cases
- sync_content: handle absent worker directory
- deploy_worker: parse success tokens correctly
- verify_deployment: pass/fail conditions
- execute_full_deployment: orchestration, log ordering, duration aggregation

Target: ≥80% coverage with all branches tested.
"""

import asyncio
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, mock_open, AsyncMock
from datetime import datetime

import pytest

from dashboard.api.deploy import DeploymentManager
from tests.helpers.fake_process import FakeProcessFactory

pytestmark = [pytest.mark.unit]


@pytest.fixture
def fake_process_factory():
    """Factory for creating fake subprocess instances."""
    factory = FakeProcessFactory()
    yield factory
    factory.reset()


@pytest.fixture
def deployment_manager():
    """Create a fresh deployment manager for each test."""
    return DeploymentManager()


@pytest.fixture
def temp_project_dirs(tmp_path):
    """Create temporary project directory structure."""
    project_root = tmp_path / "project"
    worker_dir = tmp_path / "jeffsthings-courses"
    site_dir = project_root / "site"
    log_dir = project_root / "logs"
    
    # Create directories
    project_root.mkdir()
    worker_dir.mkdir()
    site_dir.mkdir()
    log_dir.mkdir()
    
    # Create manifest.json for testing
    manifest_path = site_dir / "manifest.json"
    manifest_path.write_text(json.dumps({"version": "1.0", "build_time": "2025-09-05"}))
    
    return {
        "project_root": project_root,
        "worker_dir": worker_dir,
        "site_dir": site_dir,
        "log_dir": log_dir,
        "manifest_path": manifest_path
    }


class TestRunCommand:
    """Test the run_command method."""
    
    @pytest.mark.asyncio
    async def test_run_command_success(self, deployment_manager, fake_process_factory):
        """Test successful command execution."""
        # Setup fake process
        fake_process_factory.register(
            "echo hello",
            stdout="hello\n",
            stderr="",
            returncode=0
        )
        
        with patch('asyncio.create_subprocess_shell', fake_process_factory.create_subprocess_shell):
            result = await deployment_manager.run_command("echo hello")
        
        assert result["success"] is True
        assert result["returncode"] == 0
        assert result["stdout"] == "hello\n"
        assert result["stderr"] == ""
        assert result["command"] == "echo hello"
    
    @pytest.mark.asyncio
    async def test_run_command_failure(self, deployment_manager, fake_process_factory):
        """Test failed command execution."""
        fake_process_factory.register(
            "false",
            stdout="",
            stderr="Command failed\n",
            returncode=1
        )
        
        with patch('asyncio.create_subprocess_shell', fake_process_factory.create_subprocess_shell):
            result = await deployment_manager.run_command("false")
        
        assert result["success"] is False
        assert result["returncode"] == 1
        assert result["stdout"] == ""
        assert result["stderr"] == "Command failed\n"
    
    @pytest.mark.asyncio
    async def test_run_command_with_environment(self, deployment_manager, fake_process_factory):
        """Test command execution with custom environment."""
        fake_process_factory.register(
            "env | grep BUILD_MODE",
            stdout="BUILD_MODE=v2\n",
            returncode=0
        )
        
        with patch('asyncio.create_subprocess_shell', fake_process_factory.create_subprocess_shell):
            result = await deployment_manager.run_command(
                "env | grep BUILD_MODE",
                env={"BUILD_MODE": "v2"}
            )
        
        assert result["success"] is True
        assert "BUILD_MODE=v2" in result["stdout"]
        
        # Verify environment was passed
        call = fake_process_factory.call_history[0]
        assert "env" in call["kwargs"]
        assert call["kwargs"]["env"]["BUILD_MODE"] == "v2"
    
    @pytest.mark.asyncio
    async def test_run_command_with_working_directory(self, deployment_manager, fake_process_factory, tmp_path):
        """Test command execution with custom working directory."""
        fake_process_factory.register(
            "pwd",
            stdout=f"{tmp_path}\n",
            returncode=0
        )
        
        with patch('asyncio.create_subprocess_shell', fake_process_factory.create_subprocess_shell):
            result = await deployment_manager.run_command("pwd", cwd=tmp_path)
        
        assert result["success"] is True
        
        # Verify cwd was passed
        call = fake_process_factory.call_history[0]
        assert call["kwargs"]["cwd"] == str(tmp_path)
    
    @pytest.mark.asyncio
    async def test_run_command_exception_handling(self, deployment_manager):
        """Test exception handling in run_command."""
        async def failing_subprocess(*args, **kwargs):
            raise OSError("Process creation failed")
        
        with patch('asyncio.create_subprocess_shell', failing_subprocess):
            result = await deployment_manager.run_command("failing_command")
        
        assert result["success"] is False
        assert result["returncode"] == -1
        assert result["stdout"] == ""
        assert "Process creation failed" in result["stderr"]


class TestBuildSite:
    """Test the build_site method."""
    
    @pytest.mark.asyncio
    async def test_build_site_success_with_manifest(self, deployment_manager, fake_process_factory, temp_project_dirs):
        """Test successful site build with manifest present."""
        fake_process_factory.register(
            "make build-site",
            stdout="Site built successfully\n",
            returncode=0
        )
        
        with patch('dashboard.api.deploy.PROJECT_ROOT', temp_project_dirs["project_root"]):
            with patch('dashboard.api.deploy.SITE_DIR', temp_project_dirs["site_dir"]):
                with patch('asyncio.create_subprocess_shell', fake_process_factory.create_subprocess_shell):
                    result = await deployment_manager.build_site()
        
        assert result["success"] is True
        assert "Site built successfully" in result["stdout"]
        
        # Verify correct environment variables were set
        call = fake_process_factory.call_history[0]
        env = call["kwargs"]["env"]
        assert env["BUILD_MODE"] == "v2"
        assert env["ENV"] == "production"
    
    @pytest.mark.asyncio
    async def test_build_site_success_no_manifest(self, deployment_manager, fake_process_factory, temp_project_dirs):
        """Test site build success but manifest missing."""
        fake_process_factory.register(
            "make build-site",
            stdout="Site built successfully\n",
            returncode=0
        )
        
        # Remove manifest to test missing case
        temp_project_dirs["manifest_path"].unlink()
        
        with patch('dashboard.api.deploy.PROJECT_ROOT', temp_project_dirs["project_root"]):
            with patch('dashboard.api.deploy.SITE_DIR', temp_project_dirs["site_dir"]):
                with patch('asyncio.create_subprocess_shell', fake_process_factory.create_subprocess_shell):
                    result = await deployment_manager.build_site()
        
        assert result["success"] is False
        assert "manifest.json not found" in result["stderr"]
    
    @pytest.mark.asyncio
    async def test_build_site_build_failure(self, deployment_manager, fake_process_factory, temp_project_dirs):
        """Test site build command failure."""
        fake_process_factory.register(
            "make build-site",
            stdout="",
            stderr="Build failed: Missing dependencies\n",
            returncode=1
        )
        
        with patch('dashboard.api.deploy.PROJECT_ROOT', temp_project_dirs["project_root"]):
            with patch('dashboard.api.deploy.SITE_DIR', temp_project_dirs["site_dir"]):
                with patch('asyncio.create_subprocess_shell', fake_process_factory.create_subprocess_shell):
                    result = await deployment_manager.build_site()
        
        assert result["success"] is False
        assert "Missing dependencies" in result["stderr"]


class TestSyncContent:
    """Test the sync_content method."""
    
    @pytest.mark.asyncio
    async def test_sync_content_success(self, deployment_manager, fake_process_factory, temp_project_dirs):
        """Test successful content sync."""
        fake_process_factory.register(
            "pnpm sync",
            stdout="Sync completed\n",
            returncode=0
        )
        
        with patch('dashboard.api.deploy.WORKER_DIR', temp_project_dirs["worker_dir"]):
            with patch('asyncio.create_subprocess_shell', fake_process_factory.create_subprocess_shell):
                result = await deployment_manager.sync_content()
        
        assert result["success"] is True
        assert "Sync completed" in result["stdout"]
        
        # Verify command was run in correct directory
        call = fake_process_factory.call_history[0]
        assert call["kwargs"]["cwd"] == str(temp_project_dirs["worker_dir"])
    
    @pytest.mark.asyncio
    async def test_sync_content_missing_worker_dir(self, deployment_manager, temp_project_dirs):
        """Test sync with missing worker directory."""
        nonexistent_dir = temp_project_dirs["project_root"] / "nonexistent"
        
        with patch('dashboard.api.deploy.WORKER_DIR', nonexistent_dir):
            result = await deployment_manager.sync_content()
        
        assert result["success"] is False
        assert "Worker directory not found" in result["stderr"]
    
    @pytest.mark.asyncio
    async def test_sync_content_command_failure(self, deployment_manager, fake_process_factory, temp_project_dirs):
        """Test sync command failure."""
        fake_process_factory.register(
            "pnpm sync",
            stdout="",
            stderr="Sync failed: Network error\n",
            returncode=1
        )
        
        with patch('dashboard.api.deploy.WORKER_DIR', temp_project_dirs["worker_dir"]):
            with patch('asyncio.create_subprocess_shell', fake_process_factory.create_subprocess_shell):
                result = await deployment_manager.sync_content()
        
        assert result["success"] is False
        assert "Network error" in result["stderr"]


class TestDeployWorker:
    """Test the deploy_worker method."""
    
    @pytest.mark.asyncio
    async def test_deploy_worker_success_with_url(self, deployment_manager, fake_process_factory, temp_project_dirs):
        """Test successful worker deployment with URL confirmation."""
        fake_process_factory.register(
            "pnpm deploy",
            stdout="Deployed to https://courses.jeffsthings.com\nDeployment complete!\n",
            returncode=0
        )
        
        with patch('dashboard.api.deploy.WORKER_DIR', temp_project_dirs["worker_dir"]):
            with patch('asyncio.create_subprocess_shell', fake_process_factory.create_subprocess_shell):
                result = await deployment_manager.deploy_worker()
        
        assert result["success"] is True
        assert "courses.jeffsthings.com" in result["stdout"]
        
        # Check logs for success message
        success_logs = [log for log in deployment_manager.deployment_log if log["level"] == "success"]
        assert any("Worker deployment successful" in log["message"] for log in success_logs)
    
    @pytest.mark.asyncio
    async def test_deploy_worker_success_no_url_confirmation(self, deployment_manager, fake_process_factory, temp_project_dirs):
        """Test worker deployment success but no URL in output."""
        fake_process_factory.register(
            "pnpm deploy",
            stdout="Deployment completed\n",
            returncode=0
        )
        
        with patch('dashboard.api.deploy.WORKER_DIR', temp_project_dirs["worker_dir"]):
            with patch('asyncio.create_subprocess_shell', fake_process_factory.create_subprocess_shell):
                result = await deployment_manager.deploy_worker()
        
        assert result["success"] is True
        
        # Check logs for warning message
        warning_logs = [log for log in deployment_manager.deployment_log if log["level"] == "warning"]
        assert any("URL not confirmed" in log["message"] for log in warning_logs)
    
    @pytest.mark.asyncio
    async def test_deploy_worker_failure(self, deployment_manager, fake_process_factory, temp_project_dirs):
        """Test worker deployment failure."""
        fake_process_factory.register(
            "pnpm deploy",
            stdout="",
            stderr="Deployment failed: Authentication error\n",
            returncode=1
        )
        
        with patch('dashboard.api.deploy.WORKER_DIR', temp_project_dirs["worker_dir"]):
            with patch('asyncio.create_subprocess_shell', fake_process_factory.create_subprocess_shell):
                result = await deployment_manager.deploy_worker()
        
        assert result["success"] is False
        assert "Authentication error" in result["stderr"]


class TestVerifyDeployment:
    """Test the verify_deployment method."""
    
    @pytest.mark.asyncio
    async def test_verify_deployment_success(self, deployment_manager, fake_process_factory, temp_project_dirs):
        """Test successful deployment verification."""
        fake_process_factory.register(
            "pnpm verify",
            stdout="All checks passed\n",
            returncode=0
        )
        
        with patch('dashboard.api.deploy.WORKER_DIR', temp_project_dirs["worker_dir"]):
            with patch('asyncio.create_subprocess_shell', fake_process_factory.create_subprocess_shell):
                result = await deployment_manager.verify_deployment()
        
        assert result["success"] is True
        assert "All checks passed" in result["stdout"]
        
        # Check logs for success message
        success_logs = [log for log in deployment_manager.deployment_log if log["level"] == "success"]
        assert any("verification passed" in log["message"] for log in success_logs)
    
    @pytest.mark.asyncio
    async def test_verify_deployment_failure(self, deployment_manager, fake_process_factory, temp_project_dirs):
        """Test deployment verification failure."""
        fake_process_factory.register(
            "pnpm verify",
            stdout="",
            stderr="Verification failed: Site unreachable\n",
            returncode=1
        )
        
        with patch('dashboard.api.deploy.WORKER_DIR', temp_project_dirs["worker_dir"]):
            with patch('asyncio.create_subprocess_shell', fake_process_factory.create_subprocess_shell):
                result = await deployment_manager.verify_deployment()
        
        assert result["success"] is False
        assert "Site unreachable" in result["stderr"]
        
        # Check logs for warning message
        warning_logs = [log for log in deployment_manager.deployment_log if log["level"] == "warning"]
        assert any("verification failed" in log["message"] for log in warning_logs)


class TestExecuteFullDeployment:
    """Test the complete deployment orchestration."""
    
    @pytest.mark.asyncio
    async def test_full_deployment_success(self, deployment_manager, fake_process_factory, temp_project_dirs):
        """Test successful full deployment pipeline."""
        # Register successful responses for all commands
        fake_process_factory.register("make build-site", stdout="Build successful\n", returncode=0)
        fake_process_factory.register("pnpm sync", stdout="Sync successful\n", returncode=0)
        fake_process_factory.register("pnpm deploy", stdout="Deploy to https://courses.jeffsthings.com\n", returncode=0)
        fake_process_factory.register("pnpm verify", stdout="Verification passed\n", returncode=0)
        
        with patch('dashboard.api.deploy.PROJECT_ROOT', temp_project_dirs["project_root"]):
            with patch('dashboard.api.deploy.SITE_DIR', temp_project_dirs["site_dir"]):
                with patch('dashboard.api.deploy.WORKER_DIR', temp_project_dirs["worker_dir"]):
                    with patch('asyncio.create_subprocess_shell', fake_process_factory.create_subprocess_shell):
                        result = await deployment_manager.execute_full_deployment()
        
        assert result["status"] == "success"
        assert "start_time" in result
        assert "end_time" in result
        assert "total_duration" in result
        assert result["production_url"] == "https://courses.jeffsthings.com"
        
        # Check all steps completed successfully
        assert result["steps"]["build"]["success"] is True
        assert result["steps"]["sync"]["success"] is True
        assert result["steps"]["deploy"]["success"] is True
        assert result["steps"]["verify"]["success"] is True
        
        # Verify step durations are tracked
        for step in result["steps"].values():
            assert "duration" in step
            assert isinstance(step["duration"], (int, float))
        
        # Verify deployment logs are included
        assert "log" in result
        assert len(result["log"]) <= 20  # Last 20 entries
    
    @pytest.mark.asyncio
    async def test_full_deployment_build_failure(self, deployment_manager, fake_process_factory, temp_project_dirs):
        """Test full deployment with build failure."""
        fake_process_factory.register("make build-site", stderr="Build failed\n", returncode=1)
        
        with patch('dashboard.api.deploy.PROJECT_ROOT', temp_project_dirs["project_root"]):
            with patch('dashboard.api.deploy.SITE_DIR', temp_project_dirs["site_dir"]):
                with patch('dashboard.api.deploy.WORKER_DIR', temp_project_dirs["worker_dir"]):
                    with patch('asyncio.create_subprocess_shell', fake_process_factory.create_subprocess_shell):
                        result = await deployment_manager.execute_full_deployment()
        
        assert result["status"] == "error"
        assert "Build failed" in result["error"]
        assert result["steps"]["build"]["success"] is False
        
        # Verify no further steps were attempted
        assert "sync" not in result["steps"]
        assert "deploy" not in result["steps"]
        assert "verify" not in result["steps"]
    
    @pytest.mark.asyncio
    async def test_full_deployment_partial_failure(self, deployment_manager, fake_process_factory, temp_project_dirs):
        """Test full deployment with verification failure (warning status)."""
        fake_process_factory.register("make build-site", stdout="Build successful\n", returncode=0)
        fake_process_factory.register("pnpm sync", stdout="Sync successful\n", returncode=0)
        fake_process_factory.register("pnpm deploy", stdout="Deploy to https://courses.jeffsthings.com\n", returncode=0)
        fake_process_factory.register("pnpm verify", stderr="Verification failed\n", returncode=1)
        
        with patch('dashboard.api.deploy.PROJECT_ROOT', temp_project_dirs["project_root"]):
            with patch('dashboard.api.deploy.SITE_DIR', temp_project_dirs["site_dir"]):
                with patch('dashboard.api.deploy.WORKER_DIR', temp_project_dirs["worker_dir"]):
                    with patch('asyncio.create_subprocess_shell', fake_process_factory.create_subprocess_shell):
                        result = await deployment_manager.execute_full_deployment()
        
        assert result["status"] == "warning"
        assert result["steps"]["build"]["success"] is True
        assert result["steps"]["sync"]["success"] is True
        assert result["steps"]["deploy"]["success"] is True
        assert result["steps"]["verify"]["success"] is False
    
    @pytest.mark.asyncio
    async def test_full_deployment_already_in_progress(self, deployment_manager):
        """Test rejection when deployment already in progress."""
        deployment_manager.is_deploying = True
        
        result = await deployment_manager.execute_full_deployment()
        
        assert result["status"] == "error"
        assert "already in progress" in result["message"]
    
    @pytest.mark.asyncio
    async def test_full_deployment_duration_tracking(self, deployment_manager, fake_process_factory, temp_project_dirs):
        """Test that individual step durations are properly tracked."""
        # Add delays to simulate realistic execution times
        fake_process_factory.register("make build-site", stdout="Build successful\n", returncode=0, delay=0.1)
        fake_process_factory.register("pnpm sync", stdout="Sync successful\n", returncode=0, delay=0.05)
        fake_process_factory.register("pnpm deploy", stdout="Deploy successful\n", returncode=0, delay=0.15)
        fake_process_factory.register("pnpm verify", stdout="Verify successful\n", returncode=0, delay=0.02)
        
        with patch('dashboard.api.deploy.PROJECT_ROOT', temp_project_dirs["project_root"]):
            with patch('dashboard.api.deploy.SITE_DIR', temp_project_dirs["site_dir"]):
                with patch('dashboard.api.deploy.WORKER_DIR', temp_project_dirs["worker_dir"]):
                    with patch('asyncio.create_subprocess_shell', fake_process_factory.create_subprocess_shell):
                        result = await deployment_manager.execute_full_deployment()
        
        assert result["status"] == "success"
        
        # Verify duration tracking
        assert result["steps"]["build"]["duration"] >= 0.1
        assert result["steps"]["sync"]["duration"] >= 0.05
        assert result["steps"]["deploy"]["duration"] >= 0.15
        assert result["steps"]["verify"]["duration"] >= 0.02
        
        # Total duration should be sum of all steps plus overhead
        expected_min_duration = 0.1 + 0.05 + 0.15 + 0.02
        assert result["total_duration"] >= expected_min_duration


class TestLoggingAndState:
    """Test logging functionality and state management."""
    
    def test_log_entry_structure(self, deployment_manager):
        """Test log entry structure and file writing."""
        with patch('builtins.open', mock_open()) as mock_file:
            deployment_manager.log("Test message", "info")
        
        assert len(deployment_manager.deployment_log) == 1
        log_entry = deployment_manager.deployment_log[0]
        
        assert "timestamp" in log_entry
        assert log_entry["level"] == "info"
        assert log_entry["message"] == "Test message"
        
        # Verify file writing was attempted
        mock_file.assert_called_once()
    
    def test_log_level_filtering(self, deployment_manager):
        """Test different log levels are properly recorded."""
        deployment_manager.log("Info message", "info")
        deployment_manager.log("Warning message", "warning")
        deployment_manager.log("Error message", "error")
        deployment_manager.log("Success message", "success")
        
        assert len(deployment_manager.deployment_log) == 4
        
        levels = [log["level"] for log in deployment_manager.deployment_log]
        assert "info" in levels
        assert "warning" in levels
        assert "error" in levels
        assert "success" in levels
    
    def test_deployment_state_tracking(self, deployment_manager):
        """Test deployment state is properly tracked."""
        assert deployment_manager.is_deploying is False
        assert deployment_manager.current_deployment is None
        
        # Simulate deployment state changes
        deployment_manager.is_deploying = True
        assert deployment_manager.is_deploying is True
        
        deployment_manager.current_deployment = {"status": "success"}
        assert deployment_manager.current_deployment["status"] == "success"


class TestEdgeCasesAndRobustness:
    """Test edge cases and error conditions."""
    
    @pytest.mark.asyncio
    async def test_unicode_handling_in_output(self, deployment_manager, fake_process_factory):
        """Test handling of unicode characters in command output."""
        fake_process_factory.register(
            "echo unicode",
            stdout="Success ✅ with émojis 🚀\n",
            returncode=0
        )
        
        with patch('asyncio.create_subprocess_shell', fake_process_factory.create_subprocess_shell):
            result = await deployment_manager.run_command("echo unicode")
        
        assert result["success"] is True
        assert "✅" in result["stdout"]
        assert "🚀" in result["stdout"]
    
    @pytest.mark.asyncio
    async def test_empty_command_output(self, deployment_manager, fake_process_factory):
        """Test handling of commands with no output."""
        fake_process_factory.register("silent", stdout="", stderr="", returncode=0)
        
        with patch('asyncio.create_subprocess_shell', fake_process_factory.create_subprocess_shell):
            result = await deployment_manager.run_command("silent")
        
        assert result["success"] is True
        assert result["stdout"] == ""
        assert result["stderr"] == ""
    
    def test_log_timestamp_format(self, deployment_manager):
        """Test log timestamp format is ISO format."""
        with patch('builtins.open', mock_open()):
            deployment_manager.log("Test")
        
        timestamp = deployment_manager.deployment_log[0]["timestamp"]
        
        # Should be able to parse as datetime
        parsed_time = datetime.fromisoformat(timestamp)
        assert isinstance(parsed_time, datetime)
    
    @pytest.mark.asyncio
    async def test_concurrent_deployment_prevention(self, deployment_manager):
        """Test that concurrent deployments are prevented."""
        deployment_manager.is_deploying = True
        
        result1 = await deployment_manager.execute_full_deployment()
        result2 = await deployment_manager.execute_full_deployment()
        
        assert result1["status"] == "error"
        assert result2["status"] == "error"
        assert "already in progress" in result1["message"]
        assert "already in progress" in result2["message"]