#!/usr/bin/env python3
"""
Test dashboard/api/tasks_htmx.py - HTMX endpoints with OOB swap fragments.

Track F: HTMX Endpoints
Target: ≥75% coverage
Focus: HTMX-specific behaviors, fragment correctness, OOB swaps
"""

import json
import pytest
from unittest.mock import MagicMock, patch, Mock
from flask import Flask

from dashboard.api.tasks_htmx import (
    update_task_status_htmx,
    quick_complete_task,
    get_task_children,
    get_tasks_list_view,
    get_tasks_kanban_view,
    get_task_dependencies,
    quick_add_task,
    get_filtered_tasks,
)


@pytest.fixture
def flask_app():
    """Create minimal Flask app for testing."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    return app


@pytest.fixture
def mock_app_context(flask_app):
    """Create Flask app context for tests."""
    with flask_app.app_context():
        yield flask_app


@pytest.mark.unit
class TestUpdateTaskStatusHTMX:
    """Test update_task_status_htmx endpoint."""
    
    def test_update_status_success_with_oob_swaps(self, mock_app_context):
        """Test successful status update returns primary task + OOB swaps."""
        with mock_app_context.test_request_context("/api/tasks/task-1/status", 
                                     method="POST", 
                                     data={"status": "done"}):
            # Mock DependencyService response
            mock_result = {
                "updated_task": {
                    "id": "task-1",
                    "title": "Test Task",
                    "status": "done",
                    "course": "MATH221"
                },
                "affected_tasks": [
                    {
                        "id": "task-2", 
                        "title": "Unblocked Task",
                        "status": "todo",
                        "course": "MATH221"
                    }
                ],
                "affected_count": 1
            }
            
            with patch("dashboard.api.tasks_htmx.DependencyService") as mock_dep:
                with patch("dashboard.api.tasks_htmx.render_template") as mock_render:
                    mock_dep.update_task_status.return_value = mock_result
                    
                    # Setup template responses
                    mock_render.side_effect = [
                        '<tr id="task-1">Primary task row</tr>',  # Primary
                        '<tr id="task-2" hx-swap-oob="true">OOB task row</tr>',  # OOB task
                        '<div id="notification" hx-swap-oob="true">Success!</div>'  # OOB notification
                    ]
                    
                    result = update_task_status_htmx("task-1")
                    
                    # Should combine all HTML fragments
                    expected = (
                        '<tr id="task-1">Primary task row</tr>'
                        '<tr id="task-2" hx-swap-oob="true">OOB task row</tr>'
                        '<div id="notification" hx-swap-oob="true">Success!</div>'
                    )
                    assert result == expected
                    
                    # Verify render_template calls
                    assert mock_render.call_count == 3
                    
                    # Check primary task render
                    mock_render.assert_any_call("_task_row.html", task=mock_result["updated_task"], oob=False)
                    
                    # Check OOB task render
                    mock_render.assert_any_call("_task_row.html", task=mock_result["affected_tasks"][0], oob=True)
                    
                    # Check notification render
                    mock_render.assert_any_call(
                        "_notification.html",
                        message="✅ Task completed! 1 task(s) unblocked.",
                        type="success",
                        oob=True
                    )

    def test_update_status_missing_status_returns_error(self, mock_app_context):
        """Test missing status parameter returns 400 error."""
        with mock_app_context.test_request_context("/api/tasks/task-1/status", method="POST", data={}):
            with patch("dashboard.api.tasks_htmx.render_template") as mock_render:
                mock_render.return_value = '<div class="error">Status required</div>'
                
                result = update_task_status_htmx("task-1")
                
                assert isinstance(result, tuple)
                html, status_code = result
                assert status_code == 400
                assert "Status required" in html
                
                mock_render.assert_called_once_with("_error.html", message="Status required")

    def test_update_status_service_error_returns_error_with_blockers(self, mock_app_context):
        """Test service error with blockers returns 400 with details."""
        with mock_app_context.test_request_context("/api/tasks/task-1/status", 
                                     method="POST", 
                                     data={"status": "done"}):
            mock_result = {
                "error": "Task is blocked",
                "blockers": ["task-0", "task-2"]
            }
            
            with patch("dashboard.api.tasks_htmx.DependencyService") as mock_dep:
                with patch("dashboard.api.tasks_htmx.render_template") as mock_render:
                    mock_dep.update_task_status.return_value = mock_result
                    mock_render.return_value = '<div class="error">Task is blocked</div>'
                    
                    result = update_task_status_htmx("task-1")
                    
                    assert isinstance(result, tuple)
                    html, status_code = result
                    assert status_code == 400
                    
                    mock_render.assert_called_once_with(
                        "_error.html", 
                        message="Task is blocked", 
                        details=["task-0", "task-2"]
                    )

    def test_update_status_no_affected_tasks_no_notification(self, mock_app_context):
        """Test update with no affected tasks doesn't show notification."""
        with mock_app_context.test_request_context("/api/tasks/task-1/status", 
                                     method="POST", 
                                     data={"status": "in_progress"}):
            mock_result = {
                "updated_task": {"id": "task-1", "title": "Test", "status": "in_progress"},
                "affected_tasks": [],
                "affected_count": 0
            }
            
            with patch("dashboard.api.tasks_htmx.DependencyService") as mock_dep:
                with patch("dashboard.api.tasks_htmx.render_template") as mock_render:
                    mock_dep.update_task_status.return_value = mock_result
                    mock_render.return_value = '<tr id="task-1">Updated task</tr>'
                    
                    result = update_task_status_htmx("task-1")
                    
                    assert result == '<tr id="task-1">Updated task</tr>'
                    # Should only render primary task, no notification
                    assert mock_render.call_count == 1


@pytest.mark.unit
class TestQuickCompleteTask:
    """Test quick_complete_task endpoint."""
    
    def test_quick_complete_success_with_unblocked_tasks(self, mock_app_context):
        """Test quick complete returns completed task + unblocked tasks."""
        with mock_app_context.test_request_context("/api/tasks/task-1/complete", method="POST"):
            mock_result = {
                "completed_task": {"id": "task-1", "title": "Completed", "status": "done"},
                "unblocked_tasks": [
                    {"id": "task-2", "title": "Now available", "status": "todo"}
                ],
                "unblocked_count": 1
            }
            
            with patch("dashboard.api.tasks_htmx.DependencyService") as mock_dep:
                with patch("dashboard.api.tasks_htmx.render_template") as mock_render:
                    mock_dep.complete_task.return_value = mock_result
                    mock_render.side_effect = [
                        '<tr id="task-1">Completed task</tr>',
                        '<tr id="task-2" hx-swap-oob="true">Unblocked task</tr>',
                        '<div id="notification" hx-swap-oob="true">🎉 1 task(s) unblocked!</div>'
                    ]
                    
                    result = quick_complete_task("task-1")
                    
                    expected = (
                        '<tr id="task-1">Completed task</tr>'
                        '<tr id="task-2" hx-swap-oob="true">Unblocked task</tr>'
                        '<div id="notification" hx-swap-oob="true">🎉 1 task(s) unblocked!</div>'
                    )
                    assert result == expected

    def test_quick_complete_error_returns_error(self, mock_app_context):
        """Test quick complete with service error returns 400."""
        with mock_app_context.test_request_context("/api/tasks/invalid/complete", method="POST"):
            mock_result = {"error": "Task not found"}
            
            with patch("dashboard.api.tasks_htmx.DependencyService") as mock_dep:
                with patch("dashboard.api.tasks_htmx.render_template") as mock_render:
                    mock_dep.complete_task.return_value = mock_result
                    mock_render.return_value = '<div class="error">Task not found</div>'
                    
                    result = quick_complete_task("invalid")
                    
                    assert isinstance(result, tuple)
                    html, status_code = result
                    assert status_code == 400


@pytest.mark.unit
class TestGetTaskChildren:
    """Test get_task_children endpoint."""
    
    def test_get_children_success(self, mock_app_context):
        """Test getting children tasks for hierarchical display."""
        with mock_app_context.test_request_context("/api/tasks/parent-1/children"):
            mock_hierarchy = {
                "children_map": {
                    "parent-1": ["child-1", "child-2", "missing-child"]
                },
                "task_map": {
                    "parent-1": {"id": "parent-1", "title": "Parent"},
                    "child-1": {"id": "child-1", "title": "Child 1"},
                    "child-2": {"id": "child-2", "title": "Child 2"}
                    # Note: missing-child not in task_map to test filtering
                }
            }
            
            with patch("dashboard.api.tasks_htmx.DependencyService") as mock_dep:
                with patch("dashboard.api.tasks_htmx.render_template") as mock_render:
                    mock_dep.get_task_hierarchy.return_value = mock_hierarchy
                    mock_render.return_value = '<div>Children tasks</div>'
                    
                    result = get_task_children("parent-1")
                    
                    assert result == '<div>Children tasks</div>'
                    
                    # Should only include children that exist in task_map
                    expected_children = [
                        {"id": "child-1", "title": "Child 1"},
                        {"id": "child-2", "title": "Child 2"}
                    ]
                    mock_render.assert_called_once_with(
                        "_task_children.html",
                        parent_id="parent-1",
                        tasks=expected_children
                    )

    def test_get_children_no_children(self, mock_app_context):
        """Test getting children for task with no children."""
        with mock_app_context.test_request_context("/api/tasks/leaf-task/children"):
            mock_hierarchy = {
                "children_map": {},  # No children for any task
                "task_map": {"leaf-task": {"id": "leaf-task", "title": "Leaf"}}
            }
            
            with patch("dashboard.api.tasks_htmx.DependencyService") as mock_dep:
                with patch("dashboard.api.tasks_htmx.render_template") as mock_render:
                    mock_dep.get_task_hierarchy.return_value = mock_hierarchy
                    mock_render.return_value = '<div>No children</div>'
                    
                    result = get_task_children("leaf-task")
                    
                    mock_render.assert_called_once_with(
                        "_task_children.html",
                        parent_id="leaf-task",
                        tasks=[]
                    )


@pytest.mark.unit
class TestGetTasksListView:
    """Test get_tasks_list_view endpoint with filtering."""
    
    def test_list_view_no_filters(self, mock_app_context):
        """Test list view with no filters returns all root tasks."""
        with mock_app_context.test_request_context("/api/tasks/list"):
            mock_hierarchy = {
                "root_tasks": [
                    {"id": "task-1", "title": "Task 1", "status": "todo"},
                    {"id": "task-2", "title": "Task 2", "status": "done"}
                ]
            }
            
            with patch("dashboard.api.tasks_htmx.DependencyService") as mock_dep:
                with patch("dashboard.api.tasks_htmx.render_template") as mock_render:
                    mock_dep.get_task_hierarchy.return_value = mock_hierarchy
                    mock_render.return_value = '<div>Task list</div>'
                    
                    result = get_tasks_list_view()
                    
                    mock_dep.get_task_hierarchy.assert_called_once_with(course=None)
                    mock_render.assert_called_once_with("_task_list.html", tasks=mock_hierarchy["root_tasks"])

    def test_list_view_with_filters(self, mock_app_context):
        """Test list view with status, course, category, and assignee filters."""
        with mock_app_context.test_request_context("/api/tasks/list?course=MATH221&status=todo&category=setup&assignee=alice"):
            mock_hierarchy = {
                "root_tasks": [
                    {"id": "task-1", "title": "Task 1", "status": "todo", "category": "setup", "assignee": "alice"},
                    {"id": "task-2", "title": "Task 2", "status": "done", "category": "setup", "assignee": "alice"},
                    {"id": "task-3", "title": "Task 3", "status": "todo", "category": "review", "assignee": "alice"},
                    {"id": "task-4", "title": "Task 4", "status": "todo", "category": "setup", "assignee": "bob"}
                ]
            }
            
            with patch("dashboard.api.tasks_htmx.DependencyService") as mock_dep:
                with patch("dashboard.api.tasks_htmx.render_template") as mock_render:
                    mock_dep.get_task_hierarchy.return_value = mock_hierarchy
                    mock_render.return_value = '<div>Filtered list</div>'
                    
                    result = get_tasks_list_view()
                    
                    # Should call with course filter
                    mock_dep.get_task_hierarchy.assert_called_once_with(course="MATH221")
                    
                    # Should only pass task-1 (matches all filters)
                    expected_filtered = [{"id": "task-1", "title": "Task 1", "status": "todo", "category": "setup", "assignee": "alice"}]
                    mock_render.assert_called_once_with("_task_list.html", tasks=expected_filtered)


@pytest.mark.unit
class TestGetTasksKanbanView:
    """Test get_tasks_kanban_view endpoint."""
    
    def test_kanban_view_organizes_by_status(self, mock_app_context):
        """Test Kanban view organizes tasks by status columns."""
        with mock_app_context.test_request_context("/api/tasks/kanban?course=MATH221"):
            mock_hierarchy = {
                "task_map": {
                    "task-1": {"id": "task-1", "title": "Blocked Task", "status": "blocked"},
                    "task-2": {"id": "task-2", "title": "Todo Task", "status": "todo"},
                    "task-3": {"id": "task-3", "title": "Progress Task", "status": "in_progress"},
                    "task-4": {"id": "task-4", "title": "Done Task", "status": "done"},
                    "task-5": {"id": "task-5", "title": "Unknown Status", "status": "unknown"}  # Should be ignored
                }
            }
            
            with patch("dashboard.api.tasks_htmx.DependencyService") as mock_dep:
                with patch("dashboard.api.tasks_htmx.render_template") as mock_render:
                    mock_dep.get_task_hierarchy.return_value = mock_hierarchy
                    mock_render.return_value = '<div>Kanban board</div>'
                    
                    result = get_tasks_kanban_view()
                    
                    # Check expected kanban organization
                    expected_kanban = {
                        "blocked": [{"id": "task-1", "title": "Blocked Task", "status": "blocked"}],
                        "todo": [{"id": "task-2", "title": "Todo Task", "status": "todo"}],
                        "in_progress": [{"id": "task-3", "title": "Progress Task", "status": "in_progress"}],
                        "done": [{"id": "task-4", "title": "Done Task", "status": "done"}]
                    }
                    
                    mock_render.assert_called_once_with("_kanban_board.html", kanban=expected_kanban)


@pytest.mark.unit
class TestGetTaskDependencies:
    """Test get_task_dependencies endpoint."""
    
    def test_get_dependencies_success(self, mock_app_context):
        """Test getting dependency visualization for a task."""
        with mock_app_context.test_request_context("/api/tasks/task-1/dependencies"):
            # Mock task graph and task objects
            mock_task = Mock()
            mock_task.to_dict.return_value = {"id": "task-1", "title": "Main Task"}
            
            mock_blocker = Mock()
            mock_blocker.to_dict.return_value = {"id": "blocker-1", "title": "Blocking Task"}
            
            mock_blocked = Mock()
            mock_blocked.to_dict.return_value = {"id": "blocked-1", "title": "Blocked Task"}
            
            mock_graph = Mock()
            mock_graph.get_task.return_value = mock_task
            mock_graph.get_blockers.return_value = [mock_blocker]
            mock_graph.get_blocked_by.return_value = [mock_blocked]
            
            with patch("dashboard.api.tasks_htmx.DependencyService") as mock_dep:
                with patch("dashboard.api.tasks_htmx.render_template") as mock_render:
                    mock_dep.build_task_graph.return_value = mock_graph
                    mock_render.return_value = '<div>Dependency modal</div>'
                    
                    result = get_task_dependencies("task-1")
                    
                    assert result == '<div>Dependency modal</div>'
                    
                    mock_render.assert_called_once_with(
                        "_dependency_modal.html",
                        task={"id": "task-1", "title": "Main Task"},
                        blockers=[{"id": "blocker-1", "title": "Blocking Task"}],
                        blocks=[{"id": "blocked-1", "title": "Blocked Task"}]
                    )

    def test_get_dependencies_task_not_found(self, mock_app_context):
        """Test getting dependencies for non-existent task returns 404."""
        with mock_app_context.test_request_context("/api/tasks/missing/dependencies"):
            mock_graph = Mock()
            mock_graph.get_task.return_value = None
            
            with patch("dashboard.api.tasks_htmx.DependencyService") as mock_dep:
                with patch("dashboard.api.tasks_htmx.render_template") as mock_render:
                    mock_dep.build_task_graph.return_value = mock_graph
                    mock_render.return_value = '<div class="error">Task not found</div>'
                    
                    result = get_task_dependencies("missing")
                    
                    assert isinstance(result, tuple)
                    html, status_code = result
                    assert status_code == 404
                    mock_render.assert_called_once_with("_error.html", message="Task not found")


@pytest.mark.unit
class TestQuickAddTask:
    """Test quick_add_task endpoint."""
    
    def test_quick_add_with_title(self, mock_app_context, tmp_state_dir):
        """Test quick add task with title requirement."""
        with mock_app_context.test_request_context("/api/tasks/quick-add", 
                                     method="POST", 
                                     data={"title": "New test task"}):
            
            # Mock config and database
            with patch("dashboard.api.tasks_htmx.Config") as mock_config:
                with patch("dashboard.api.tasks_htmx.Database") as mock_db_class:
                    with patch("dashboard.api.tasks_htmx.DatabaseConfig") as mock_db_config:
                        with patch("dashboard.api.tasks_htmx.DependencyService") as mock_dep:
                            with patch("dashboard.api.tasks_htmx.render_template") as mock_render:
                                
                                # Setup mocks
                                mock_config.STATE_DIR = tmp_state_dir
                                mock_config.TASKS_FILE = tmp_state_dir / "tasks.json"
                                
                                mock_db = Mock()
                                mock_db_class.return_value = mock_db
                                
                                mock_hierarchy = {"root_tasks": [{"id": "new-task", "title": "New test task"}]}
                                mock_dep.get_task_hierarchy.return_value = mock_hierarchy
                                mock_render.return_value = '<div>Updated task list</div>'
                                
                                result = quick_add_task()
                                
                                # Verify database operations
                                mock_db.initialize.assert_called_once()
                                mock_db.create_task.assert_called_once()
                                
                                # Check task creation arguments
                                create_call = mock_db.create_task.call_args[0][0]
                                assert create_call["course"] == "MATH221"  # Default
                                assert create_call["title"] == "New test task"
                                assert create_call["status"] == "todo"
                                
                                assert result == '<div>Updated task list</div>'

    def test_quick_add_empty_title_returns_error(self, mock_app_context):
        """Test quick add with empty title returns 400."""
        with mock_app_context.test_request_context("/api/tasks/quick-add", method="POST", data={"title": "  "}):
            with patch("dashboard.api.tasks_htmx.render_template") as mock_render:
                mock_render.return_value = '<div class="error">Title required</div>'
                
                result = quick_add_task()
                
                assert isinstance(result, tuple)
                html, status_code = result
                assert status_code == 400

    def test_quick_add_detects_course_code(self, mock_app_context, tmp_state_dir):
        """Test quick add detects course code in title."""
        with mock_app_context.test_request_context("/api/tasks/quick-add", 
                                     method="POST", 
                                     data={"title": "STAT253 Review distributions"}):
            
            with patch("dashboard.api.tasks_htmx.Config") as mock_config:
                with patch("dashboard.api.tasks_htmx.Database") as mock_db_class:
                    with patch("dashboard.api.tasks_htmx.DatabaseConfig"):
                        with patch("dashboard.api.tasks_htmx.DependencyService") as mock_dep:
                            with patch("dashboard.api.tasks_htmx.render_template") as mock_render:
                                
                                mock_config.STATE_DIR = tmp_state_dir
                                mock_config.TASKS_FILE = tmp_state_dir / "tasks.json"
                                
                                mock_db = Mock()
                                mock_db_class.return_value = mock_db
                                
                                mock_hierarchy = {"root_tasks": []}
                                mock_dep.get_task_hierarchy.return_value = mock_hierarchy
                                mock_render.return_value = '<div>Task list</div>'
                                
                                result = quick_add_task()
                                
                                # Check that course was detected and title cleaned
                                create_call = mock_db.create_task.call_args[0][0]
                                assert create_call["course"] == "STAT253"
                                assert create_call["title"] == "Review distributions"  # Course code removed

    def test_quick_add_handles_db_exceptions(self, mock_app_context, tmp_state_dir, caplog_debug):
        """Test quick add handles database initialization and export exceptions gracefully."""
        with mock_app_context.test_request_context("/api/tasks/quick-add", 
                                     method="POST", 
                                     data={"title": "Test task"}):
            
            with patch("dashboard.api.tasks_htmx.Config") as mock_config:
                with patch("dashboard.api.tasks_htmx.Database") as mock_db_class:
                    with patch("dashboard.api.tasks_htmx.DatabaseConfig"):
                        with patch("dashboard.api.tasks_htmx.DependencyService") as mock_dep:
                            with patch("dashboard.api.tasks_htmx.render_template") as mock_render:
                                
                                mock_config.STATE_DIR = tmp_state_dir
                                mock_config.TASKS_FILE = tmp_state_dir / "tasks.json"
                                
                                # Mock DB with exceptions
                                mock_db = Mock()
                                mock_db.initialize.side_effect = Exception("DB init failed")
                                mock_db.export_snapshot_to_json.side_effect = Exception("Export failed")
                                mock_db_class.return_value = mock_db
                                
                                mock_hierarchy = {"root_tasks": []}
                                mock_dep.get_task_hierarchy.return_value = mock_hierarchy
                                mock_render.return_value = '<div>Task list</div>'
                                
                                result = quick_add_task()
                                
                                # Should still succeed despite exceptions
                                assert result == '<div>Task list</div>'
                                
                                # Check that warnings/debug messages were logged
                                assert "DB init warning" in caplog_debug.text
                                assert "Snapshot export skipped" in caplog_debug.text


@pytest.mark.unit
class TestGetFilteredTasks:
    """Test get_filtered_tasks endpoint with multiple filter types."""
    
    def test_filtered_tasks_all_filters(self, mock_app_context):
        """Test filtered tasks with all filter types applied."""
        with mock_app_context.test_request_context(
            "/api/tasks/filtered?course=MATH221&status=todo&category=setup&assignee=alice"
        ):
            mock_hierarchy = {
                "task_map": {
                    "task-1": {"id": "task-1", "status": "todo", "category": "setup", "assignee": "alice"},
                    "task-2": {"id": "task-2", "status": "done", "category": "setup", "assignee": "alice"},
                    "task-3": {"id": "task-3", "status": "todo", "category": "review", "assignee": "alice"},
                    "task-4": {"id": "task-4", "status": "todo", "category": "setup", "assignee": "bob"}
                }
            }
            
            with patch("dashboard.api.tasks_htmx.DependencyService") as mock_dep:
                with patch("dashboard.api.tasks_htmx.render_template") as mock_render:
                    mock_dep.get_task_hierarchy.return_value = mock_hierarchy
                    mock_render.return_value = '<div>Filtered tasks</div>'
                    
                    result = get_filtered_tasks()
                    
                    # Should filter to only task-1
                    expected_filtered = [{"id": "task-1", "status": "todo", "category": "setup", "assignee": "alice"}]
                    mock_render.assert_called_once_with("_task_list.html", tasks=expected_filtered)

    def test_filtered_tasks_overdue_filter(self, mock_app_context, frozen_time):
        """Test overdue filter for tasks past due date."""
        with mock_app_context.test_request_context("/api/tasks/filtered?filter=overdue"):
            # frozen_time is at 2025-09-01, so 2025-08-30 is overdue
            mock_hierarchy = {
                "task_map": {
                    "task-1": {"id": "task-1", "due_date": "2025-08-30", "status": "todo"},  # Overdue
                    "task-2": {"id": "task-2", "due_date": "2025-09-02", "status": "todo"},  # Future
                    "task-3": {"id": "task-3", "due_date": "2025-08-25", "status": "done"},   # Overdue but done
                    "task-4": {"id": "task-4", "due_date": None, "status": "todo"}           # No due date
                }
            }
            
            with patch("dashboard.api.tasks_htmx.DependencyService") as mock_dep:
                with patch("dashboard.api.tasks_htmx.render_template") as mock_render:
                    mock_dep.get_task_hierarchy.return_value = mock_hierarchy
                    mock_render.return_value = '<div>Overdue tasks</div>'
                    
                    result = get_filtered_tasks()
                    
                    # Should only include task-1 (overdue and not done)
                    expected_filtered = [{"id": "task-1", "due_date": "2025-08-30", "status": "todo"}]
                    mock_render.assert_called_once_with("_task_list.html", tasks=expected_filtered)

    def test_filtered_tasks_critical_path_filter(self, mock_app_context):
        """Test critical path filter."""
        with mock_app_context.test_request_context("/api/tasks/filtered?filter=critical-path&course=MATH221"):
            mock_hierarchy = {
                "task_map": {
                    "task-1": {"id": "task-1", "title": "Critical 1"},
                    "task-2": {"id": "task-2", "title": "Regular Task"},
                    "task-3": {"id": "task-3", "title": "Critical 2"}
                }
            }
            
            critical_tasks = [
                {"id": "task-1", "title": "Critical 1"},
                {"id": "task-3", "title": "Critical 2"}
            ]
            
            with patch("dashboard.api.tasks_htmx.DependencyService") as mock_dep:
                with patch("dashboard.api.tasks_htmx.render_template") as mock_render:
                    mock_dep.get_task_hierarchy.return_value = mock_hierarchy
                    mock_dep.get_critical_path.return_value = critical_tasks
                    mock_render.return_value = '<div>Critical path tasks</div>'
                    
                    result = get_filtered_tasks()
                    
                    # Should only include critical path tasks
                    expected_filtered = [
                        {"id": "task-1", "title": "Critical 1"},
                        {"id": "task-3", "title": "Critical 2"}
                    ]
                    mock_render.assert_called_once_with("_task_list.html", tasks=expected_filtered)

    def test_filtered_tasks_kanban_view(self, mock_app_context):
        """Test filtered tasks with view=kanban returns kanban template."""
        with mock_app_context.test_request_context("/api/tasks/filtered?view=kanban"):
            mock_hierarchy = {
                "task_map": {
                    "task-1": {"id": "task-1", "status": "todo"},
                    "task-2": {"id": "task-2", "status": "done"},
                    "task-3": {"id": "task-3", "status": "blocked"}
                }
            }
            
            with patch("dashboard.api.tasks_htmx.DependencyService") as mock_dep:
                with patch("dashboard.api.tasks_htmx.render_template") as mock_render:
                    mock_dep.get_task_hierarchy.return_value = mock_hierarchy
                    mock_render.return_value = '<div>Kanban view</div>'
                    
                    result = get_filtered_tasks()
                    
                    # Should organize by status and render kanban template
                    expected_kanban = {
                        "blocked": [{"id": "task-3", "status": "blocked"}],
                        "todo": [{"id": "task-1", "status": "todo"}],
                        "in_progress": [],
                        "done": [{"id": "task-2", "status": "done"}]
                    }
                    mock_render.assert_called_once_with("_kanban_board.html", kanban=expected_kanban)

    def test_filtered_tasks_hierarchical_organization(self, mock_app_context):
        """Test filtered tasks organizes root tasks hierarchically."""
        with mock_app_context.test_request_context("/api/tasks/filtered"):
            mock_hierarchy = {
                "task_map": {
                    "task-1": {"id": "task-1", "title": "Root Task", "parent_id": None},
                    "task-2": {"id": "task-2", "title": "Child Task", "parent_id": "task-1"},
                    "task-3": {"id": "task-3", "title": "Another Root", "parent_id": None}
                }
            }
            
            with patch("dashboard.api.tasks_htmx.DependencyService") as mock_dep:
                with patch("dashboard.api.tasks_htmx.render_template") as mock_render:
                    mock_dep.get_task_hierarchy.return_value = mock_hierarchy
                    mock_render.return_value = '<div>Hierarchical tasks</div>'
                    
                    result = get_filtered_tasks()
                    
                    # Should only include root tasks (no parent_id)
                    expected_root_tasks = [
                        {"id": "task-1", "title": "Root Task", "parent_id": None},
                        {"id": "task-3", "title": "Another Root", "parent_id": None}
                    ]
                    mock_render.assert_called_once_with("_task_list.html", tasks=expected_root_tasks)


@pytest.mark.unit
class TestHTMXBehaviors:
    """Test HTMX-specific behaviors and response patterns."""
    
    def test_oob_swap_attributes_in_templates(self, mock_app_context):
        """Test that OOB swap attributes are correctly set."""
        with mock_app_context.test_request_context("/api/tasks/task-1/status", 
                                     method="POST", 
                                     data={"status": "done"}):
            mock_result = {
                "updated_task": {"id": "task-1", "title": "Test"},
                "affected_tasks": [{"id": "task-2", "title": "Affected"}],
                "affected_count": 1
            }
            
            with patch("dashboard.api.tasks_htmx.DependencyService") as mock_dep:
                with patch("dashboard.api.tasks_htmx.render_template") as mock_render:
                    mock_dep.update_task_status.return_value = mock_result
                    
                    # Track template calls to verify OOB parameter usage
                    template_calls = []
                    def track_render(template, **kwargs):
                        template_calls.append((template, kwargs))
                        return f'<div>{template}</div>'
                    
                    mock_render.side_effect = track_render
                    
                    result = update_task_status_htmx("task-1")
                    
                    # Verify primary task rendered without OOB
                    primary_call = template_calls[0]
                    assert primary_call[0] == "_task_row.html"
                    assert primary_call[1]["oob"] is False
                    
                    # Verify affected task rendered with OOB
                    affected_call = template_calls[1]
                    assert affected_call[0] == "_task_row.html"
                    assert affected_call[1]["oob"] is True
                    
                    # Verify notification rendered with OOB
                    notification_call = template_calls[2]
                    assert notification_call[0] == "_notification.html"
                    assert notification_call[1]["oob"] is True

    def test_response_combines_multiple_fragments(self, mock_app_context):
        """Test that responses correctly combine multiple HTML fragments."""
        with mock_app_context.test_request_context("/api/tasks/task-1/complete", method="POST"):
            mock_result = {
                "completed_task": {"id": "task-1", "title": "Done"},
                "unblocked_tasks": [
                    {"id": "task-2", "title": "Unblocked 1"},
                    {"id": "task-3", "title": "Unblocked 2"}
                ],
                "unblocked_count": 2
            }
            
            with patch("dashboard.api.tasks_htmx.DependencyService") as mock_dep:
                with patch("dashboard.api.tasks_htmx.render_template") as mock_render:
                    mock_dep.complete_task.return_value = mock_result
                    
                    # Return different fragments for each template call
                    mock_render.side_effect = [
                        '<tr id="task-1" class="completed">Completed</tr>',
                        '<tr id="task-2" hx-swap-oob="true">Unblocked 1</tr>',
                        '<tr id="task-3" hx-swap-oob="true">Unblocked 2</tr>',
                        '<div id="notification" hx-swap-oob="true">Success!</div>'
                    ]
                    
                    result = quick_complete_task("task-1")
                    
                    # Should combine all fragments in order
                    expected = (
                        '<tr id="task-1" class="completed">Completed</tr>'
                        '<tr id="task-2" hx-swap-oob="true">Unblocked 1</tr>'
                        '<tr id="task-3" hx-swap-oob="true">Unblocked 2</tr>'
                        '<div id="notification" hx-swap-oob="true">Success!</div>'
                    )
                    assert result == expected