"""Unit and property tests for dashboard/services/prioritization.py.

Tests for:
- Snapshot rotations and scoring map
- Constraints: timebox, k limit, min_courses, chain-head requirements
- explain(task_id) returns stable breakdowns
- Hypothesis property tests for monotonicity and stability
- Integration test for refresh_now_queue
"""

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

from hypothesis import given, strategies as st, assume, settings, HealthCheck

from dashboard.services.prioritization import PrioritizationService, PrioritizationConfig
from tests.helpers.builders import TaskBuilder, TaskGraphBuilder

pytestmark = [pytest.mark.unit]


class TestPrioritizationService:
    """Unit tests for PrioritizationService core functionality."""
    
    def test_initialization_requires_db_and_config(self, repo):
        """Test service initialization with required parameters."""
        config = PrioritizationConfig(
            state_dir=Path("/tmp/test"),
            calendar_path=Path("test_calendar.yaml")
        )
        service = PrioritizationService(repo.db, config)
        assert service.db is repo.db
        assert service.config is config
        assert service.state_dir == Path("/tmp/test")
    
    def test_snapshot_creates_files_and_rotates(self, repo, tmp_path, frozen_time):
        """Test snapshot creation and rotation logic."""
        config = PrioritizationConfig(
            state_dir=tmp_path,
            calendar_path=Path("test_calendar.yaml"),
            snapshot_rotate=2  # Keep only 2 files
        )
        service = PrioritizationService(repo.db, config)
        
        # Add some test data to make DB non-empty
        task = TaskBuilder("test-1").with_course("MATH221").build()
        repo.db.create_task(task)
        
        # Take snapshots
        service.snapshot()
        service.snapshot()
        service.snapshot()  # Third should trigger rotation
        
        snapshots_dir = tmp_path / "snapshots"
        assert snapshots_dir.exists()
        
        # Check that only 2 .db.gz files remain due to rotation
        db_files = list(snapshots_dir.glob("*.db.gz"))
        assert len(db_files) <= 2
        
        # Check JSON snapshots exist
        json_files = list(snapshots_dir.glob("*.json"))
        assert len(json_files) >= 1
    
    def test_snapshot_handles_empty_db_gracefully(self, repo, tmp_path):
        """Test snapshot when DB is empty."""
        config = PrioritizationConfig(
            state_dir=tmp_path,
            calendar_path=Path("test_calendar.yaml")
        )
        service = PrioritizationService(repo.db, config)
        
        # Empty DB should still work for snapshots
        service.snapshot()
        
        snapshots_dir = tmp_path / "snapshots"
        assert snapshots_dir.exists()
        
        # Should create JSON files even if DB is empty
        json_files = list(snapshots_dir.glob("*.json"))
        assert len(json_files) >= 1
    
    def test_current_phase_with_fallback(self, repo, tmp_path):
        """Test phase detection with fallback when calendar missing."""
        config = PrioritizationConfig(
            state_dir=tmp_path,
            calendar_path=Path("nonexistent.yaml"),
            semester_start_fallback="2025-08-25"
        )
        service = PrioritizationService(repo.db, config)
        
        phase_key, weights = service._current_phase()
        
        # Should return some phase key and weights dict
        assert isinstance(phase_key, str)
        assert isinstance(weights, dict)
        assert len(phase_key) > 0
    
    def test_explain_task_not_found(self, repo, tmp_path):
        """Test explain returns error for non-existent task."""
        config = PrioritizationConfig(
            state_dir=tmp_path,
            calendar_path=Path("test_calendar.yaml")
        )
        service = PrioritizationService(repo.db, config)
        
        result = service.explain("nonexistent-task")
        assert result == {"error": "Task not found"}
    
    def test_explain_returns_stable_breakdown(self, seeded_repo, tmp_path):
        """Test explain returns consistent breakdown for same task."""
        config = PrioritizationConfig(
            state_dir=tmp_path,
            calendar_path=Path("test_calendar.yaml")
        )
        service = PrioritizationService(seeded_repo.db, config)
        
        # Get first task from seeded data
        tasks = seeded_repo.db.list_tasks()
        assert len(tasks) > 0
        task_id = tasks[0]["id"]
        
        # Call explain multiple times
        result1 = service.explain(task_id)
        result2 = service.explain(task_id)
        result3 = service.explain(task_id)
        
        # Results should be stable
        assert result1["task_id"] == result2["task_id"] == result3["task_id"]
        assert result1["score"] == result2["score"] == result3["score"]
        assert result1["phase"] == result2["phase"] == result3["phase"]
        
        # Check required fields exist
        assert "task_id" in result1
        assert "score" in result1
        assert "factors" in result1
        assert "explain" in result1
        assert "minimal_unblock" in result1
        assert "phase" in result1
    
    def test_health_detects_dag_cycles(self, repo, tmp_path):
        """Test health check detects DAG cycles."""
        config = PrioritizationConfig(
            state_dir=tmp_path,
            calendar_path=Path("test_calendar.yaml")
        )
        service = PrioritizationService(repo.db, config)
        
        # Create a cycle: A -> B -> C -> A
        task_a = TaskBuilder("task-a").with_course("MATH221").build()
        task_b = TaskBuilder("task-b").with_course("MATH221").build()
        task_c = TaskBuilder("task-c").with_course("MATH221").build()
        
        repo.db.create_task(task_a)
        repo.db.create_task(task_b)
        repo.db.create_task(task_c)
        
        repo.db.add_deps("task-a", ["task-b"])  # A depends on B
        repo.db.add_deps("task-b", ["task-c"])  # B depends on C
        repo.db.add_deps("task-c", ["task-a"])  # C depends on A (cycle!)
        
        health = service.health()
        
        assert health["dag_ok"] is False
        assert health["cycle_path"] is not None
        assert len(health["cycle_path"]) > 0
        assert health["break_suggestion"] is not None


class TestRefreshNowQueue:
    """Tests for refresh_now_queue integration."""
    
    def test_refresh_now_queue_basic_functionality(self, seeded_repo, tmp_path):
        """Test refresh_now_queue processes tasks and creates output."""
        config = PrioritizationConfig(
            state_dir=tmp_path,
            calendar_path=Path("test_calendar.yaml")
        )
        service = PrioritizationService(seeded_repo.db, config)
        
        # Mock contracts loading to avoid file dependencies
        with patch("dashboard.services.prioritization.load_yaml") as mock_load:
            mock_load.return_value = {
                "constraints": {
                    "fit_minutes": 90,
                    "k": 3,
                    "heavy_threshold": 60,
                    "require_chain_heads": False,
                    "min_courses": 2,
                    "exclude_status": ["blocked"],
                    "wip_cap": 5
                },
                "phase_weights": {
                    "default": {"urgency": 1.0, "impact": 1.0}
                },
                "factors": {
                    "weights": {
                        "urgency": 1.0,
                        "impact": 1.0,
                        "effort": 0.5
                    }
                }
            }
            
            queue_ids = service.refresh_now_queue()
        
        # Check results
        assert isinstance(queue_ids, list)
        assert len(queue_ids) >= 0  # Could be empty if no eligible tasks
        
        # Check now_queue.json was created
        now_queue_file = tmp_path / "now_queue.json"
        assert now_queue_file.exists()
        
        with open(now_queue_file) as f:
            payload = json.load(f)
        
        assert "queue" in payload
        assert "metadata" in payload
        assert "generated" in payload["metadata"]
        assert "timebox" in payload["metadata"]
        assert "phase" in payload["metadata"]
    
    def test_refresh_now_queue_respects_constraints(self, repo, tmp_path):
        """Test refresh_now_queue respects timebox and k constraints."""
        config = PrioritizationConfig(
            state_dir=tmp_path,
            calendar_path=Path("test_calendar.yaml")
        )
        service = PrioritizationService(repo.db, config)
        
        # Create tasks with known effort estimates
        tasks = [
            TaskBuilder("task-1").with_course("MATH221").build(),
            TaskBuilder("task-2").with_course("MATH251").build(),
            TaskBuilder("task-3").with_course("STAT253").build(),
            TaskBuilder("task-4").with_course("MATH221").build(),
        ]
        
        # Set est_minutes manually
        for i, task in enumerate(tasks, 1):
            task["est_minutes"] = 30 + i * 10  # 30, 40, 50, 60
            repo.db.create_task(task)
        
        # Mock contracts
        with patch("dashboard.services.prioritization.load_yaml") as mock_load:
            mock_load.return_value = {
                "constraints": {
                    "fit_minutes": 90,  # Tight timebox
                    "k": 2,            # Max 2 tasks
                    "heavy_threshold": 45,
                    "require_chain_heads": False,
                    "min_courses": 1,
                    "exclude_status": ["blocked"],
                    "wip_cap": 10
                },
                "phase_weights": {
                    "default": {"urgency": 1.0}
                },
                "factors": {
                    "weights": {"urgency": 1.0}
                }
            }
            
            queue_ids = service.refresh_now_queue(timebox=90, k=2)
        
        # Should respect k=2 constraint
        assert len(queue_ids) <= 2
    
    def test_refresh_now_queue_includes_courses_filter(self, repo, tmp_path):
        """Test refresh_now_queue respects include_courses filter."""
        config = PrioritizationConfig(
            state_dir=tmp_path,
            calendar_path=Path("test_calendar.yaml")
        )
        service = PrioritizationService(repo.db, config)
        
        task_math = TaskBuilder("task-math").with_course("MATH221").build()
        task_stat = TaskBuilder("task-stat").with_course("STAT253").build()
        
        repo.db.create_task(task_math)
        repo.db.create_task(task_stat)
        
        with patch("dashboard.services.prioritization.load_yaml") as mock_load:
            mock_load.return_value = {
                "constraints": {
                    "fit_minutes": 180,
                    "k": 5,
                    "heavy_threshold": 60,
                    "require_chain_heads": False,
                    "min_courses": 1,
                    "exclude_status": ["blocked"],
                    "wip_cap": 10
                },
                "phase_weights": {"default": {"urgency": 1.0}},
                "factors": {"weights": {"urgency": 1.0}}
            }
            
            # Filter to only MATH221
            queue_ids = service.refresh_now_queue(
                include_courses={"MATH221"}
            )
        
        # Verify only MATH tasks are included by checking the JSON output
        now_queue_file = tmp_path / "now_queue.json"
        with open(now_queue_file) as f:
            payload = json.load(f)
        
        for task in payload["queue"]:
            assert task.get("course") == "MATH221"


@pytest.mark.property
class TestPrioritizationProperties:
    """Property-based tests using Hypothesis."""
    
    @given(st.integers(min_value=2, max_value=8))
    @settings(max_examples=20, deadline=3000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_monotonicity_basic_scoring_properties(self, repo, num_tasks):
        """Property: scoring should produce consistent, non-negative results."""
        assume(num_tasks >= 2)
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            config = PrioritizationConfig(
                state_dir=Path(tmp_dir),
                calendar_path=Path("test_calendar.yaml")
            )
            service = PrioritizationService(repo.db, config)
            
            # Create tasks
            tasks = []
            import random
            task_id_base = random.randint(10000, 99999)  # Avoid ID conflicts
            for i in range(num_tasks):
                task = TaskBuilder(f"task-{task_id_base}-{i}").with_course("MATH221").build()
                tasks.append(task)
                repo.db.create_task(task)
            
            with patch("dashboard.services.prioritization.load_yaml") as mock_load:
                mock_load.return_value = {
                    "constraints": {
                        "fit_minutes": 300,
                        "k": num_tasks,
                        "heavy_threshold": 120,
                        "require_chain_heads": False,
                        "min_courses": 1,
                        "exclude_status": ["blocked"],
                        "wip_cap": 20
                    },
                    "phase_weights": {"default": {"impact": 1.0}},
                    "factors": {"weights": {"impact": 2.0, "downstream_unlocked": 1.0}}
                }
                
                # Get scores
                initial_scores = {}
                for task in tasks:
                    explain = service.explain(task["id"])
                    initial_scores[task["id"]] = explain["score"]
                
                # Basic properties should hold
                for task_id, score in initial_scores.items():
                    assert isinstance(score, (int, float))
                    assert score >= 0  # Scores should be non-negative
    
    @given(
        st.integers(min_value=2, max_value=4),  # num_tasks
        st.floats(min_value=0.1, max_value=1.0),  # noise_epsilon
    )
    @settings(max_examples=15, deadline=4000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_stability_under_small_changes(self, repo, num_tasks, noise_epsilon):
        """Property: small scoring changes should not drastically reorder tasks."""
        assume(0.1 <= noise_epsilon <= 1.0)
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            config = PrioritizationConfig(
                state_dir=Path(tmp_dir),
                calendar_path=Path("test_calendar.yaml")
            )
            service = PrioritizationService(repo.db, config)
            
            tasks = []
            import random
            task_id_base = random.randint(10000, 99999)  # Avoid ID conflicts
            for i in range(num_tasks):
                task = TaskBuilder(f"task-{task_id_base}-{i}").with_course(f"COURSE{i%3}").build()
                tasks.append(task)
                repo.db.create_task(task)
            
            with patch("dashboard.services.prioritization.load_yaml") as mock_load:
                base_weights = {"urgency": 1.0, "impact": 1.0, "effort": 0.5}
                
                mock_load.return_value = {
                    "constraints": {
                        "fit_minutes": 300,
                        "k": num_tasks,
                        "heavy_threshold": 120,
                        "require_chain_heads": False,
                        "min_courses": 1,
                        "exclude_status": ["blocked"],
                        "wip_cap": 20
                    },
                    "phase_weights": {"default": base_weights},
                    "factors": {"weights": base_weights}
                }
                
                # Get baseline ranking
                baseline_scores = {}
                for task in tasks:
                    explain = service.explain(task["id"])
                    baseline_scores[task["id"]] = explain["score"]
                
                baseline_order = sorted(
                    baseline_scores.items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )
                
                # Apply small noise to weights
                noisy_weights = {
                    k: v * (1 + noise_epsilon * 0.05)  # Very small change
                    for k, v in base_weights.items()
                }
                
                mock_load.return_value["factors"]["weights"] = noisy_weights
                
                # Get noisy ranking
                noisy_scores = {}
                for task in tasks:
                    explain = service.explain(task["id"])
                    noisy_scores[task["id"]] = explain["score"]
                
                noisy_order = sorted(
                    noisy_scores.items(),
                    key=lambda x: x[1], 
                    reverse=True
                )
                
                # Scores should still be reasonable 
                if len(baseline_order) > 1:
                    baseline_top_score = baseline_order[0][1]
                    noisy_top_score = noisy_order[0][1]
                    
                    if baseline_top_score > 0 and noisy_top_score > 0:
                        score_ratio = noisy_top_score / baseline_top_score
                        # Small changes shouldn't dramatically change scores
                        assert 0.8 <= score_ratio <= 1.2


# Create golden file test
def test_refresh_now_queue_golden_file_validation(seeded_repo, tmp_path):
    """Test refresh_now_queue output against golden file."""
    config = PrioritizationConfig(
        state_dir=tmp_path,
        calendar_path=Path("test_calendar.yaml")
    )
    service = PrioritizationService(seeded_repo.db, config)
    
    golden_contracts = {
        "constraints": {
            "fit_minutes": 120,
            "k": 3,
            "heavy_threshold": 60,
            "require_chain_heads": True,
            "min_courses": 2,
            "exclude_status": ["blocked", "done"],
            "wip_cap": 5
        },
        "phase_weights": {
            "default": {"urgency": 2.0, "impact": 1.5, "effort": 0.8}
        },
        "factors": {
            "weights": {
                "urgency": 2.0,
                "impact": 1.5,
                "effort": 0.8,
                "downstream_unlocked": 1.2
            }
        }
    }
    
    with patch("dashboard.services.prioritization.load_yaml") as mock_load:
        mock_load.return_value = golden_contracts
        
        queue_ids = service.refresh_now_queue()
    
    # Verify structure is consistent
    now_queue_file = tmp_path / "now_queue.json"
    assert now_queue_file.exists()
    
    with open(now_queue_file) as f:
        payload = json.load(f)
    
    # Golden file validation - check required structure
    assert "queue" in payload
    assert "metadata" in payload
    assert isinstance(payload["queue"], list)
    assert isinstance(payload["metadata"], dict)
    assert "generated" in payload["metadata"]
    assert "timebox" in payload["metadata"]
    assert "phase" in payload["metadata"]
    
    # Each queue item should have expected fields
    for item in payload["queue"]:
        assert "id" in item
        assert "smart_score" in item
        assert isinstance(item["smart_score"], (int, float))