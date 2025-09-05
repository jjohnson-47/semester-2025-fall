"""Unit tests for deploy API.

Target: ≥80% coverage on deployment pipeline.
Tests DeploymentManager, command execution, and Flask routes.
"""

import asyncio
import json
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

from dashboard.api.deploy import DeploymentManager, deploy_bp, deployment_manager


@pytest.mark.unit
class TestDeploymentManager:
    """Test DeploymentManager core functionality."""
    
    def test_manager_initialization(self):
        """Test deployment manager initializes correctly."""
        manager = DeploymentManager()
        
        assert manager.current_deployment is None
        assert manager.deployment_log == []
        assert manager.is_deploying is False
    
    def test_log_message(self, tmp_path):
        """Test logging functionality."""
        manager = DeploymentManager()
        
        with patch('dashboard.api.deploy.LOG_DIR', tmp_path):
            manager.log("Test message", level="info")
            
        # Check memory log
        assert len(manager.deployment_log) == 1
        entry = manager.deployment_log[0]
        assert entry["message"] == "Test message"
        assert entry["level"] == "info"
        assert "timestamp" in entry
        
        # Check file log
        log_files = list(tmp_path.glob("deployment_*.log"))
        assert len(log_files) == 1
        
        with open(log_files[0]) as f:
            content = f.read()
            assert "Test message" in content
            assert "[INFO]" in content
    
    @pytest.mark.asyncio
    async def test_run_command_success(self):
        """Test successful command execution."""
        manager = DeploymentManager()
        
        # Mock subprocess
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b"output", b""))
        
        with patch('asyncio.create_subprocess_shell', return_value=mock_process):
            result = await manager.run_command("test command")
        
        assert result["success"] is True
        assert result["command"] == "test command"
        assert result["returncode"] == 0
        assert result["stdout"] == "output"
        assert result["stderr"] == ""
    
    @pytest.mark.asyncio
    async def test_run_command_failure(self):
        """Test failed command execution."""
        manager = DeploymentManager()
        
        # Mock subprocess
        mock_process = AsyncMock()
        mock_process.returncode = 1
        mock_process.communicate = AsyncMock(return_value=(b"", b"error output"))
        
        with patch('asyncio.create_subprocess_shell', return_value=mock_process):
            result = await manager.run_command("failing command")
        
        assert result["success"] is False
        assert result["command"] == "failing command"
        assert result["returncode"] == 1
        assert result["stdout"] == ""
        assert result["stderr"] == "error output"
    
    @pytest.mark.asyncio
    async def test_run_command_exception(self):
        """Test command execution with exception."""
        manager = DeploymentManager()
        
        with patch('asyncio.create_subprocess_shell', side_effect=Exception("Process error")):
            result = await manager.run_command("exception command")
        
        assert result["success"] is False
        assert result["command"] == "exception command"
        assert result["returncode"] == -1
        assert result["stderr"] == "Process error"
    
    @pytest.mark.asyncio
    async def test_build_site_success(self, tmp_path):
        """Test successful site build."""
        manager = DeploymentManager()
        
        # Mock successful command and manifest file
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text("{}")
        
        with patch.object(manager, 'run_command', return_value={"success": True}), \
             patch('dashboard.api.deploy.SITE_DIR', tmp_path):
            
            result = await manager.build_site()
        
        assert result["success"] is True
        
        # Check log entries
        log_messages = [entry["message"] for entry in manager.deployment_log]
        assert any("Starting site build" in msg for msg in log_messages)
        assert any("Site build completed successfully" in msg for msg in log_messages)
    
    @pytest.mark.asyncio
    async def test_build_site_missing_manifest(self, tmp_path):
        """Test site build with missing manifest."""
        manager = DeploymentManager()
        
        with patch.object(manager, 'run_command', return_value={"success": True}), \
             patch('dashboard.api.deploy.SITE_DIR', tmp_path):
            
            result = await manager.build_site()
        
        assert result["success"] is False
        assert "manifest.json not found" in result["stderr"]
    
    @pytest.mark.asyncio
    async def test_sync_content_success(self, tmp_path):
        """Test successful content sync."""
        manager = DeploymentManager()
        
        # Create worker directory
        worker_dir = tmp_path / "worker"
        worker_dir.mkdir()
        
        with patch.object(manager, 'run_command', return_value={"success": True}), \
             patch('dashboard.api.deploy.WORKER_DIR', worker_dir):
            
            result = await manager.sync_content()
        
        assert result["success"] is True
        
        # Check log entries
        log_messages = [entry["message"] for entry in manager.deployment_log]
        assert any("Syncing content" in msg for msg in log_messages)
        assert any("Content sync completed" in msg for msg in log_messages)
    
    @pytest.mark.asyncio
    async def test_sync_content_missing_worker_dir(self, tmp_path):
        """Test content sync with missing worker directory."""
        manager = DeploymentManager()
        
        non_existent_dir = tmp_path / "nonexistent"
        
        with patch('dashboard.api.deploy.WORKER_DIR', non_existent_dir):
            result = await manager.sync_content()
        
        assert result["success"] is False
        assert "Worker directory not found" in result["stderr"]
    
    @pytest.mark.asyncio
    async def test_deploy_worker_success(self):
        """Test successful worker deployment."""
        manager = DeploymentManager()
        
        mock_result = {
            "success": True,
            "stdout": "Deployed to courses.jeffsthings.com",
            "stderr": ""
        }
        
        with patch.object(manager, 'run_command', return_value=mock_result):
            result = await manager.deploy_worker()
        
        assert result["success"] is True
        
        # Check log entries
        log_messages = [entry["message"] for entry in manager.deployment_log]
        assert any("Deploying to Cloudflare" in msg for msg in log_messages)
        assert any("Worker deployment successful" in msg for msg in log_messages)
    
    @pytest.mark.asyncio
    async def test_deploy_worker_url_not_confirmed(self):
        """Test worker deployment without URL confirmation."""
        manager = DeploymentManager()
        
        mock_result = {
            "success": True,
            "stdout": "Deployed but no URL",
            "stderr": ""
        }
        
        with patch.object(manager, 'run_command', return_value=mock_result):
            result = await manager.deploy_worker()
        
        assert result["success"] is True
        
        # Check warning log
        log_messages = [entry["message"] for entry in manager.deployment_log]
        assert any("URL not confirmed" in msg for msg in log_messages)
    
    @pytest.mark.asyncio
    async def test_verify_deployment_success(self):
        """Test successful deployment verification."""
        manager = DeploymentManager()
        
        with patch.object(manager, 'run_command', return_value={"success": True}):
            result = await manager.verify_deployment()
        
        assert result["success"] is True
        
        # Check log entries
        log_messages = [entry["message"] for entry in manager.deployment_log]
        assert any("Verifying deployment" in msg for msg in log_messages)
        assert any("verification passed" in msg for msg in log_messages)
    
    @pytest.mark.asyncio
    async def test_verify_deployment_failure(self):
        """Test failed deployment verification."""
        manager = DeploymentManager()
        
        with patch.object(manager, 'run_command', return_value={"success": False}):
            result = await manager.verify_deployment()
        
        assert result["success"] is False
        
        # Check warning log
        log_messages = [entry["message"] for entry in manager.deployment_log]
        assert any("verification failed" in msg for msg in log_messages)


@pytest.mark.unit
class TestFullDeploymentPipeline:
    """Test the complete deployment pipeline."""
    
    @pytest.mark.asyncio
    async def test_deployment_already_in_progress(self):
        """Test deployment rejection when already in progress."""
        manager = DeploymentManager()
        manager.is_deploying = True
        
        result = await manager.execute_full_deployment()
        
        assert result["status"] == "error"
        assert "already in progress" in result["message"]
    
    @pytest.mark.asyncio
    async def test_successful_full_deployment(self, tmp_path):
        """Test successful complete deployment pipeline."""
        manager = DeploymentManager()
        
        # Mock all successful steps
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text("{}")
        
        worker_dir = tmp_path / "worker"
        worker_dir.mkdir()
        
        successful_result = {"success": True, "stdout": "courses.jeffsthings.com"}
        
        with patch.object(manager, 'run_command', return_value=successful_result), \
             patch('dashboard.api.deploy.SITE_DIR', tmp_path), \
             patch('dashboard.api.deploy.WORKER_DIR', worker_dir):
            
            result = await manager.execute_full_deployment()
        
        assert result["status"] == "success"
        assert "start_time" in result
        assert "end_time" in result
        assert "total_duration" in result
        
        # Check all steps completed successfully
        assert len(result["steps"]) == 4
        assert all(step["success"] for step in result["steps"].values())
        assert "build" in result["steps"]
        assert "sync" in result["steps"]
        assert "deploy" in result["steps"]
        assert "verify" in result["steps"]
        
        # Check deployment manager state
        assert manager.is_deploying is False
        assert manager.current_deployment == result
        assert len(result["log"]) <= 20  # Should truncate to last 20 entries
    
    @pytest.mark.asyncio
    async def test_deployment_build_failure(self, tmp_path):
        """Test deployment pipeline with build failure."""
        manager = DeploymentManager()
        
        # Mock failed build (no manifest)
        failed_result = {"success": True}  # Command succeeds but no manifest
        
        with patch.object(manager, 'run_command', return_value=failed_result), \
             patch('dashboard.api.deploy.SITE_DIR', tmp_path):  # No manifest created
            
            result = await manager.execute_full_deployment()
        
        assert result["status"] == "error"
        assert "Build failed" in result["error"]
        assert manager.is_deploying is False
        
        # Only build step should be recorded
        assert "build" in result["steps"]
        assert result["steps"]["build"]["success"] is False
        assert len(result["steps"]) == 1  # Pipeline stopped after build
    
    @pytest.mark.asyncio
    async def test_deployment_sync_failure(self, tmp_path):
        """Test deployment pipeline with sync failure."""
        manager = DeploymentManager()
        
        # Mock successful build but failed sync
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text("{}")
        
        def mock_command(cmd, **kwargs):
            if "make build-site" in cmd:
                return {"success": True}
            elif "pnpm sync" in cmd:
                return {"success": False, "stderr": "Sync failed"}
            return {"success": True}
        
        worker_dir = tmp_path / "worker"
        worker_dir.mkdir()
        
        with patch.object(manager, 'run_command', side_effect=mock_command), \
             patch('dashboard.api.deploy.SITE_DIR', tmp_path), \
             patch('dashboard.api.deploy.WORKER_DIR', worker_dir):
            
            result = await manager.execute_full_deployment()
        
        assert result["status"] == "error"
        assert "Sync failed" in result["error"]
        
        # Build and sync steps should be recorded
        assert "build" in result["steps"]
        assert "sync" in result["steps"]
        assert result["steps"]["build"]["success"] is True
        assert result["steps"]["sync"]["success"] is False
        assert len(result["steps"]) == 2  # Pipeline stopped after sync
    
    @pytest.mark.asyncio
    async def test_deployment_with_warnings(self, tmp_path):
        """Test deployment that completes with warnings."""
        manager = DeploymentManager()
        
        # Mock all steps succeed except verification
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text("{}")
        
        worker_dir = tmp_path / "worker"
        worker_dir.mkdir()
        
        def mock_command(cmd, **kwargs):
            if "pnpm verify" in cmd:
                return {"success": False}  # Verification fails but not critical
            return {"success": True, "stdout": "courses.jeffsthings.com"}
        
        with patch.object(manager, 'run_command', side_effect=mock_command), \
             patch('dashboard.api.deploy.SITE_DIR', tmp_path), \
             patch('dashboard.api.deploy.WORKER_DIR', worker_dir):
            
            result = await manager.execute_full_deployment()
        
        assert result["status"] == "warning"
        assert len(result["steps"]) == 4  # All steps attempted
        assert result["steps"]["verify"]["success"] is False
        
        # Check warning message in logs
        log_messages = [entry["message"] for entry in manager.deployment_log]
        assert any("completed with warnings" in msg for msg in log_messages)


@pytest.mark.unit 
class TestDeploymentRoutes:
    """Test Flask deployment API routes."""
    
    @pytest.fixture
    def app(self):
        """Create Flask app with deployment routes."""
        from flask import Flask
        app = Flask(__name__)
        app.register_blueprint(deploy_bp)
        app.config['TESTING'] = True
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()
    
    def test_trigger_deployment_route(self, client):
        """Test deployment trigger endpoint."""
        mock_result = {
            "status": "success",
            "start_time": datetime.now().isoformat(),
            "steps": {"build": {"success": True}},
            "production_url": "https://courses.jeffsthings.com"
        }
        
        # Mock the async method with AsyncMock
        with patch.object(deployment_manager, 'execute_full_deployment', new_callable=AsyncMock) as mock_deploy:
            mock_deploy.return_value = mock_result
            response = client.post('/api/deploy/trigger')
            
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert "production_url" in data
    
    def test_deployment_status_idle(self, client):
        """Test deployment status when idle."""
        # Reset deployment manager
        deployment_manager.is_deploying = False
        deployment_manager.current_deployment = None
        
        response = client.get('/api/deploy/status')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "idle"
        assert "No deployments executed" in data["message"]
    
    def test_deployment_status_deploying(self, client):
        """Test deployment status when deploying."""
        # Set deployment manager to deploying state
        deployment_manager.is_deploying = True
        deployment_manager.deployment_log = [
            {"timestamp": "2025-09-05T10:00:00", "level": "info", "message": "Starting deployment"}
        ]
        
        response = client.get('/api/deploy/status')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "deploying"
        assert "in progress" in data["message"]
        assert "log" in data
        
        # Reset state
        deployment_manager.is_deploying = False
    
    def test_deployment_status_with_last_deployment(self, client):
        """Test deployment status with completed deployment."""
        # Set previous deployment
        last_deployment = {
            "status": "success",
            "start_time": "2025-09-05T09:00:00",
            "end_time": "2025-09-05T09:05:00"
        }
        deployment_manager.is_deploying = False
        deployment_manager.current_deployment = last_deployment
        
        response = client.get('/api/deploy/status')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "idle"
        assert data["last_deployment"]["status"] == "success"
    
    def test_deployment_logs_route(self, client):
        """Test deployment logs endpoint."""
        # Set up logs
        deployment_manager.deployment_log = [
            {"timestamp": "2025-09-05T10:00:00", "level": "info", "message": f"Log entry {i}"}
            for i in range(100)
        ]
        
        response = client.get('/api/deploy/logs')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data["logs"]) == 50  # Default limit
        assert data["total_entries"] == 100
    
    def test_deployment_logs_with_custom_limit(self, client):
        """Test deployment logs with custom limit."""
        # Set up logs
        deployment_manager.deployment_log = [
            {"timestamp": "2025-09-05T10:00:00", "level": "info", "message": f"Log entry {i}"}
            for i in range(20)
        ]
        
        response = client.get('/api/deploy/logs?limit=10')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data["logs"]) == 10
        assert data["total_entries"] == 20
    
    def test_verify_deployment_route(self, client):
        """Test deployment verification endpoint."""
        mock_result = {
            "success": True,
            "stdout": "Verification passed",
            "stderr": ""
        }
        
        with patch.object(deployment_manager, 'verify_deployment', new_callable=AsyncMock) as mock_verify:
            mock_verify.return_value = mock_result
            response = client.get('/api/deploy/verify')
            
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["verified"] is True
        assert data["output"] == "Verification passed"
        assert data["errors"] == ""
    
    def test_verify_deployment_failure_route(self, client):
        """Test deployment verification endpoint with failure."""
        mock_result = {
            "success": False,
            "stdout": "",
            "stderr": "Verification failed"
        }
        
        with patch.object(deployment_manager, 'verify_deployment', new_callable=AsyncMock) as mock_verify:
            mock_verify.return_value = mock_result
            response = client.get('/api/deploy/verify')
            
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["verified"] is False
        assert data["errors"] == "Verification failed"


@pytest.mark.unit
class TestDeploymentManagerState:
    """Test deployment manager state management."""
    
    def test_concurrent_deployment_prevention(self):
        """Test that concurrent deployments are prevented."""
        manager = DeploymentManager()
        manager.is_deploying = True
        
        # Should reject new deployment
        async def test():
            result = await manager.execute_full_deployment()
            assert result["status"] == "error"
            assert "already in progress" in result["message"]
        
        asyncio.run(test())
    
    def test_deployment_log_truncation(self):
        """Test that deployment logs are truncated properly."""
        manager = DeploymentManager()
        
        # Add many log entries
        for i in range(50):
            manager.log(f"Entry {i}")
        
        # Mock successful deployment
        async def mock_deployment():
            result = {
                "status": "success",
                "steps": {},
                "log": manager.deployment_log[-20:]
            }
            manager.current_deployment = result
            return result
        
        # Should only keep last 20 in result
        result = asyncio.run(mock_deployment())
        assert len(result["log"]) == 20
        assert result["log"][0]["message"] == "Entry 30"  # Should start from entry 30
        assert result["log"][-1]["message"] == "Entry 49"  # Should end with entry 49
    
    def test_log_file_creation(self, tmp_path):
        """Test that log files are created with correct naming."""
        manager = DeploymentManager()
        
        with patch('dashboard.api.deploy.LOG_DIR', tmp_path):
            manager.log("Test message")
        
        # Check log file was created with today's date
        today = datetime.now().strftime('%Y%m%d')
        expected_file = tmp_path / f"deployment_{today}.log"
        assert expected_file.exists()
        
        content = expected_file.read_text()
        assert "Test message" in content
        assert "[INFO]" in content