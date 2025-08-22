#!/usr/bin/env python3
"""
HTMX-specific task endpoints with out-of-band swap support.
Implements dependency-aware updates following HTMX 2.x patterns.
"""

from flask import render_template, request

from dashboard.api import api_bp
from dashboard.services.dependency_service import DependencyService


@api_bp.route("/tasks/<task_id>/status", methods=["POST"])
def update_task_status_htmx(task_id):
    """
    Update task status with HTMX out-of-band swaps for unblocked tasks.
    Returns the updated task row plus any affected task rows.
    """
    new_status = request.form.get("status")

    if not new_status:
        return render_template("_error.html", message="Status required"), 400

    # Update status and get affected tasks
    result = DependencyService.update_task_status(task_id, new_status)

    if "error" in result:
        return render_template(
            "_error.html", message=result["error"], details=result.get("blockers")
        ), 400

    # Render the primary task row
    primary_html = render_template("_task_row.html", task=result["updated_task"], oob=False)

    # Render out-of-band updates for affected tasks
    oob_html = ""
    for affected_task in result.get("affected_tasks", []):
        oob_html += render_template("_task_row.html", task=affected_task, oob=True)

    # If task was marked done, show a success notification
    if new_status == "done" and result.get("affected_count", 0) > 0:
        oob_html += render_template(
            "_notification.html",
            message=f"✅ Task completed! {result['affected_count']} task(s) unblocked.",
            type="success",
            oob=True,
        )

    return primary_html + oob_html


@api_bp.route("/tasks/<task_id>/complete", methods=["POST"])
def quick_complete_task(task_id):
    """
    Quick complete a task with dependency resolution.
    Returns updated rows for all affected tasks.
    """
    result = DependencyService.complete_task(task_id)

    if "error" in result:
        return render_template("_error.html", message=result["error"]), 400

    # Render the completed task
    completed_html = render_template("_task_row.html", task=result["completed_task"], oob=False)

    # Render unblocked tasks with OOB swaps
    oob_html = ""
    for unblocked_task in result.get("unblocked_tasks", []):
        oob_html += render_template("_task_row.html", task=unblocked_task, oob=True)

    # Add notification if tasks were unblocked
    if result.get("unblocked_count", 0) > 0:
        oob_html += render_template(
            "_notification.html",
            message=f"🎉 {result['unblocked_count']} task(s) unblocked!",
            type="success",
            oob=True,
        )

    return completed_html + oob_html


@api_bp.route("/tasks/<task_id>/children", methods=["GET"])
def get_task_children(task_id):
    """
    Get children tasks for hierarchical display.
    Used for lazy-loading child tasks when expanding a parent.
    """
    hierarchy = DependencyService.get_task_hierarchy()

    # Find children of this task
    children_ids = hierarchy["children_map"].get(task_id, [])
    children_tasks = [
        hierarchy["task_map"][child_id]
        for child_id in children_ids
        if child_id in hierarchy["task_map"]
    ]

    return render_template("_task_children.html", parent_id=task_id, tasks=children_tasks)


@api_bp.route("/tasks/list", methods=["GET"])
def get_tasks_list_view():
    """Get tasks in list view format."""
    course = request.args.get("course")
    status = request.args.get("status")
    category = request.args.get("category")
    assignee = request.args.get("assignee")

    hierarchy = DependencyService.get_task_hierarchy(course=course)

    # Apply filters
    tasks = hierarchy["root_tasks"]

    if status:
        tasks = [t for t in tasks if t["status"] == status]
    if category:
        tasks = [t for t in tasks if t["category"] == category]
    if assignee:
        tasks = [t for t in tasks if t.get("assignee") == assignee]

    return render_template("_task_list.html", tasks=tasks)


@api_bp.route("/tasks/kanban", methods=["GET"])
def get_tasks_kanban_view():
    """Get tasks in Kanban board view format."""
    course = request.args.get("course")

    hierarchy = DependencyService.get_task_hierarchy(course=course)
    all_tasks = list(hierarchy["task_map"].values())

    # Organize by status columns
    kanban = {"blocked": [], "todo": [], "in_progress": [], "done": []}

    for task in all_tasks:
        status = task["status"]
        if status in kanban:
            kanban[status].append(task)

    return render_template("_kanban_board.html", kanban=kanban)


@api_bp.route("/tasks/<task_id>/dependencies", methods=["GET"])
def get_task_dependencies(task_id):
    """
    Get dependency visualization for a task.
    Shows what blocks this task and what this task blocks.
    """
    graph = DependencyService.build_task_graph()
    task = graph.get_task(task_id)

    if not task:
        return render_template("_error.html", message="Task not found"), 404

    blockers = graph.get_blockers(task_id)
    blocked_by_this = graph.get_blocked_by(task_id)

    return render_template(
        "_dependency_modal.html",
        task=task.to_dict(),
        blockers=[b.to_dict() for b in blockers],
        blocks=[b.to_dict() for b in blocked_by_this],
    )


@api_bp.route("/tasks/quick-add", methods=["POST"])
def quick_add_task():
    """
    Quick add a task from the command palette.
    Returns the updated task list.
    """
    from dashboard.services.task_service import TaskService

    title = request.form.get("title", "").strip()
    if not title:
        return render_template("_error.html", message="Title required"), 400

    # Parse title for course code
    course = "MATH221"  # Default
    for code in ["MATH221", "MATH251", "STAT253"]:
        if code in title.upper():
            course = code
            title = title.replace(code, "").replace(code.lower(), "").strip()
            break

    # Create task
    task_data = {
        "course": course,
        "title": title,
        "status": "todo",
        "priority": "medium",
        "category": "setup",
    }

    TaskService.create_task(task_data)

    # Return updated task list
    hierarchy = DependencyService.get_task_hierarchy()
    return render_template("_task_list.html", tasks=hierarchy["root_tasks"])


@api_bp.route("/tasks/filtered", methods=["GET"])
def get_filtered_tasks():
    """
    Get filtered tasks based on multiple criteria.
    Used by the filter bar with live updates.
    """
    course = request.args.get("course")
    status = request.args.get("status")
    category = request.args.get("category")
    assignee = request.args.get("assignee")
    filter_type = request.args.get("filter")

    hierarchy = DependencyService.get_task_hierarchy(course=course)
    all_tasks = list(hierarchy["task_map"].values())

    # Apply filters
    if status:
        all_tasks = [t for t in all_tasks if t["status"] == status]
    if category:
        all_tasks = [t for t in all_tasks if t["category"] == category]
    if assignee:
        all_tasks = [t for t in all_tasks if t.get("assignee") == assignee]

    # Special filters
    if filter_type == "overdue":
        from datetime import date

        today = date.today()
        all_tasks = [
            t
            for t in all_tasks
            if t.get("due_date")
            and date.fromisoformat(t["due_date"]) < today
            and t["status"] != "done"
        ]
    elif filter_type == "critical-path":
        critical_tasks = DependencyService.get_critical_path(course=course)
        critical_ids = {t["id"] for t in critical_tasks}
        all_tasks = [t for t in all_tasks if t["id"] in critical_ids]

    # Organize hierarchically
    root_tasks = [t for t in all_tasks if not t.get("parent_id")]

    # Determine view type
    view = request.args.get("view", "list")
    if view == "kanban":
        # Organize by status for Kanban
        kanban = {"blocked": [], "todo": [], "in_progress": [], "done": []}
        for task in all_tasks:
            if task["status"] in kanban:
                kanban[task["status"]].append(task)
        return render_template("_kanban_board.html", kanban=kanban)
    else:
        return render_template("_task_list.html", tasks=root_tasks)
