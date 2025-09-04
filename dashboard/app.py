#!/usr/bin/env python3
"""Course Setup Dashboard - Flask Application.

A comprehensive task management system for semester course preparation that integrates
with the syllabus generation system. Provides a web interface for tracking course
setup tasks, viewing generated syllabi, and managing semester preparation workflow.

Architecture:
    - Flask web framework with Jinja2 templating
    - JSON file-based storage with file locking for concurrent access
    - Environment-based configuration with python-dotenv
    - Integration with build system for syllabus serving
    - Optional git snapshots for state history

Main Components:
    - Routes: Dashboard views and API endpoints
    - Templates: Bootstrap-based responsive UI
    - Config: Environment-aware configuration

Usage:
    From project root:
        uv run python dashboard/app.py

    Or using make:
        make dash

Environment Variables:
    DASH_PORT (int): Server port (default: 5055)
    DASH_HOST (str): Server host (default: 127.0.0.1)
    DASH_AUTO_SNAPSHOT (bool): Enable git snapshots (default: true)
    PROJECT_ROOT (str): Project root path (auto-detected)
    BUILD_DIR (str): Build output directory (default: build)
    SYLLABI_DIR (str): Syllabi directory (default: build/syllabi)

See dashboard/API_DOCUMENTATION.md for complete API reference.
"""

import contextlib
import json

# Set up logging
import logging
import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, cast

import pytz  # type: ignore[import-untyped]
from flask import Flask, Response, jsonify, render_template, request, send_file, send_from_directory
from flask.typing import ResponseReturnValue

from dashboard.config import Config
from dashboard.db import Database, DatabaseConfig
from dashboard.orchestrator import AgentCoordinator, TaskOrchestrator
from dashboard.services.prioritization import PrioritizationConfig, PrioritizationService
from dashboard.services.retro import generate_weekly_retro

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)

# Initialize orchestrator
orchestrator = TaskOrchestrator(state_dir=Config.STATE_DIR)
agent_coordinator = AgentCoordinator(orchestrator)

# Database repository (DB-first; optional one-time JSON bootstrap)
DB_PATH = Config.STATE_DIR / "tasks.db"
_db = Database(DatabaseConfig(DB_PATH))
try:  # best-effort init — does not fail the app
    _db.initialize()
except Exception as _exc:  # pragma: no cover
    logger.warning("SQLite repo init warning: %s", _exc)
else:
    # Auto-import from JSON if DB is empty but tasks.json exists
    try:
        with _db.connect() as _c:
            cnt = _c.execute("select count(*) from tasks").fetchone()[0]
        if int(cnt) == 0 and (Config.STATE_DIR / "tasks.json").exists():
            _db.import_tasks_json(Config.STATE_DIR / "tasks.json")
            logger.info("Imported tasks.json into SQLite (bootstrap)")
    except Exception as _imp_exc:  # pragma: no cover
        logger.warning("Bootstrap import skipped: %s", _imp_exc)

# Prioritization service (DB-backed), keeps JSON now_queue export in sync
_prio = PrioritizationService(
    _db,
    PrioritizationConfig(state_dir=Config.STATE_DIR, calendar_path=Path("academic-calendar.json")),
)

# Optional in-process scheduler (graceful if missing)
try:
    from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore

    _scheduler = BackgroundScheduler(daemon=True)
    # Hourly refresh (lightweight enough locally)
    _scheduler.add_job(
        lambda: _prio.refresh_now_queue(timebox=90, k=3),
        "interval",
        hours=1,
        id="hourly_refresh",
        replace_existing=True,
    )
    # Morning refresh at 08:00 local
    _scheduler.add_job(
        lambda: _prio.refresh_now_queue(timebox=90, k=3),
        "cron",
        hour=8,
        minute=0,
        id="morning_refresh",
        replace_existing=True,
    )
    # Weekly retro Sunday 17:00 local
    _scheduler.add_job(
        lambda: generate_weekly_retro(_db, Config.STATE_DIR / "retro"),
        "cron",
        day_of_week="sun",
        hour=17,
        minute=0,
        id="weekly_retro",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info("APScheduler started with hourly + morning refresh jobs")
except Exception as _sched_exc:  # pragma: no cover
    logger.info("Scheduler not active: %s", _sched_exc)

# Note: The more advanced API is exposed via the package factory in
# dashboard/__init__.py. This module-level app provides lightweight endpoints
# against the SQLite repository.

# Configuration from Config class
TIMEZONE = pytz.timezone(Config.TIMEZONE)
STATE_DIR = Config.STATE_DIR
TASKS_FILE = Config.TASKS_FILE
COURSES_FILE = Config.COURSES_FILE
AUTO_SNAPSHOT = Config.AUTO_SNAPSHOT

# Ensure state directory exists
STATE_DIR.mkdir(exist_ok=True)


def load_courses() -> dict[str, Any]:
    """Load courses configuration from COURSES_FILE."""
    if not COURSES_FILE.exists():
        return {"courses": []}
    try:
        return json.loads(COURSES_FILE.read_text())
    except Exception:
        return {"courses": []}


def _legacy_tasks_from_json() -> list[dict[str, Any]]:
    """Load legacy tasks from tasks.json if present (testing/back-compat only)."""
    path = STATE_DIR / "tasks.json"
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text())
        return list(payload.get("tasks", []))
    except Exception:
        return []


def calculate_progress(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    """Calculate overall progress statistics."""
    total = len(tasks)
    if total == 0:
        return {"total": 0, "completed": 0, "percentage": 0}

    completed = sum(1 for t in tasks if t.get("status") == "completed")
    percentage = (completed / total) * 100

    return {"total": total, "completed": completed, "percentage": round(percentage, 2)}


def get_upcoming_deadlines(tasks: list[dict[str, Any]], days: int = 7) -> list[dict[str, Any]]:
    """Get tasks with deadlines in the next N days."""
    upcoming = []
    cutoff_date = datetime.now() + timedelta(days=days)

    for task in tasks:
        if "due_date" in task and task.get("status") != "completed":
            try:
                due_date = datetime.fromisoformat(task["due_date"])
                if due_date <= cutoff_date:
                    upcoming.append(task)
            except (ValueError, TypeError):
                continue

    return sorted(upcoming, key=lambda t: t["due_date"])


def calculate_priority(task: dict[str, Any]) -> int:
    """Calculate task priority based on due date and weight."""
    priority: int = int(task.get("weight", 1))

    if "due" in task:
        try:
            due_date = datetime.fromisoformat(task["due"])
            days_until = (due_date - datetime.now()).days

            if days_until < 0:  # Overdue
                priority += 100
            elif days_until == 0:  # Due today
                priority += 50
            elif days_until <= 3:  # Due soon
                priority += 20
            elif days_until <= 7:  # Due this week
                priority += 10
        except (ValueError, TypeError, AttributeError) as e:
            logger.debug(f"Date parsing error in priority calculation: {e}")
            pass

    return priority


def get_status_color(status: str) -> str:
    """Get color class for status."""
    colors = {
        "blocked": "secondary",
        "todo": "primary",
        "doing": "warning",
        "review": "info",
        "done": "success",
    }
    return colors.get(status, "light")


def get_due_color(task: dict[str, Any]) -> str:
    """Get color class based on due date."""
    if "due" not in task:
        return ""

    try:
        due_date = datetime.fromisoformat(task["due"])
        days_until = (due_date - datetime.now()).days

        if days_until < 0:
            return "danger"  # Overdue
        elif days_until == 0:
            return "warning"  # Due today
        elif days_until <= 3:
            return "info"  # Due soon
        elif days_until <= 7:
            return "primary"  # Due this week
    except (ValueError, TypeError, AttributeError) as e:
        logger.debug(f"Date parsing error in color calculation: {e}")
        pass

    return ""


# Backwards-compatible helper for tests expecting module-level function
def validate_task_data(task: dict[str, Any]) -> bool:
    """Validate task structure (fields required by API/tests)."""
    required_fields = ["course", "title", "status", "priority"]
    return all(field in task for field in required_fields)


@app.route("/")
def index() -> str:
    """Main dashboard view (DB-backed with JSON Now Queue compatibility)."""
    # Load tasks from DB and enrich with scores for display ordering
    tasks = _db.list_tasks()
    score_map: dict[str, float] = {}
    with _db.connect() as conn:
        for r in conn.execute("select task_id, score from scores").fetchall():
            score_map[r["task_id"]] = float(r["score"])  # type: ignore[index]
        # Identify quick-added tasks via events
        qa_rows = conn.execute(
            "select distinct task_id from events where field='source' and to_val='quick_add'"
        ).fetchall()
        quick_added_ids = {r["task_id"] for r in qa_rows}
    for t in tasks:
        if t.get("id") in score_map:
            t["smart_score"] = score_map[t["id"]]
        if t.get("id") in quick_added_ids:
            t["quick_added"] = True
    courses = load_courses()

    # Load Now Queue (export JSON) if it exists
    now_queue = []
    now_queue_file = STATE_DIR / "now_queue.json"
    if now_queue_file.exists():
        with open(now_queue_file) as f:
            now_queue_data = json.load(f)
            all_queue_tasks = now_queue_data.get("queue", [])
            # Filter out completed tasks from Now Queue
            now_queue = [
                task for task in all_queue_tasks if task.get("status") not in ["done", "completed"]
            ]
            # Annotate quick-added based on events
            for q in now_queue:
                if q.get("id") in quick_added_ids:
                    q["quick_added"] = True

    # Calculate priorities and add display helpers
    for task in tasks:
        # Use smart_score if available, otherwise calculate basic priority
        if "smart_score" not in task:
            task["priority"] = calculate_priority(task)
        else:
            task["priority"] = task["smart_score"]

        task["status_color"] = get_status_color(task.get("status", "todo"))
        task["due_color"] = get_due_color(task)

        # Format due date for display
        if "due_date" in task or "due_at" in task:
            try:
                due_str = task.get("due_date") or task.get("due_at")
                due = datetime.fromisoformat(due_str)
                task["due_display"] = due.strftime("%b %d, %Y")
                task["due_relative"] = get_relative_time(due)
            except (ValueError, TypeError, AttributeError) as e:
                logger.debug(f"Failed to format due date for task {task.get('id')}: {e}")
                task["due_display"] = task.get("due_date") or task.get("due_at") or ""
        elif "due" in task:  # Fallback for old format
            try:
                due = datetime.fromisoformat(task["due"])
                task["due_display"] = due.strftime("%b %d, %Y")
                task["due_relative"] = get_relative_time(due)
            except (ValueError, TypeError, AttributeError) as e:
                logger.debug(f"Failed to format due date for task {task.get('id')}: {e}")
                task["due_display"] = task["due"]

    # Sort by smart_score/priority
    tasks.sort(key=lambda t: t.get("smart_score", t.get("priority", 0)), reverse=True)

    # Group by course
    by_course: dict[str, list] = {}
    for task in tasks:
        course = task.get("course", "General")
        if course not in by_course:
            by_course[course] = []
        by_course[course].append(task)

    # Calculate stats
    stats = {
        "total": len(tasks),
        "blocked": sum(1 for t in tasks if t.get("status") == "blocked"),
        "todo": sum(1 for t in tasks if t.get("status") == "todo"),
        "doing": sum(1 for t in tasks if t.get("status") == "doing"),
        "review": sum(1 for t in tasks if t.get("status") == "review"),
        "done": sum(1 for t in tasks if t.get("status") == "done"),
        "overdue": sum(1 for t in tasks if t.get("due_color") == "danger"),
    }

    return cast(
        str,
        render_template(
            "dashboard.html",
            tasks=tasks,
            by_course=by_course,
            courses=courses.get("courses", []),
            stats=stats,
            updated=datetime.now().isoformat(),
            now_queue=now_queue,
        ),
    )


# --- JSON API (DB-backed) ---
@app.route("/api/tasks", methods=["GET"])
def api_get_tasks() -> ResponseReturnValue:
    """Return tasks from DB with optional course/status filters."""
    course = request.args.get("course")
    status = request.args.get("status")
    # Map legacy statuses to DB canonical
    if status in {"in_progress", "in-progress", "progress"}:
        status = "doing"
    if status in {"completed", "complete"}:
        status = "done"
    tasks = _db.list_tasks(status=status, course=course)
    # In tests, allow falling back to legacy JSON if DB is empty
    if app.config.get("TESTING") and not tasks:
        legacy = _legacy_tasks_from_json()
        if legacy:
            # Apply filters in-memory with same status mapping
            filtered = legacy
            if course:
                filtered = [t for t in filtered if t.get("course") == course]
            if status:
                # Legacy may use completed/in_progress
                def _map_status(s: str) -> str:
                    if s in {"in_progress", "in-progress", "progress"}:
                        return "doing"
                    if s in {"completed", "complete"}:
                        return "done"
                    return s

                filtered = [t for t in filtered if _map_status(str(t.get("status", ""))) == status]
            tasks = filtered
    return jsonify({"tasks": tasks, "metadata": {"source": "sqlite"}})


@app.route("/api/tasks", methods=["POST"])
def api_create_task() -> ResponseReturnValue:
    """Create a new task and persist it to DB (and export JSON snapshot)."""
    payload = request.get_json(silent=True) or {}
    required = ["course", "title", "status"]
    missing = [f for f in required if f not in payload]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400
    # Map status
    if payload.get("status") in {"in_progress", "in-progress", "progress"}:
        payload["status"] = "doing"
    if payload.get("status") in {"completed", "complete"}:
        payload["status"] = "done"
    task_id = _db.create_task(payload)
    # Log create event
    _db.add_event(task_id, "create", None, "created")
    # Export snapshot for UI compatibility
    _db.export_snapshot_to_json(TASKS_FILE)
    return jsonify({"id": task_id}), 201


@app.route("/api/tasks/<task_id>", methods=["PUT"])
def api_update_task(task_id: str) -> ResponseReturnValue:
    """Update a task (status/fields) in DB and export snapshot."""
    body = request.get_json(silent=True) or {}
    existing = _db.get_task(task_id)
    if not existing:
        return jsonify({"error": "Task not found"}), 404

    allowed = {
        "status",
        "title",
        "due_at",
        "est_minutes",
        "weight",
        "category",
        "notes",
        "checklist",
    }
    updates = {k: v for k, v in body.items() if k in allowed}
    if not updates:
        return jsonify({"error": "No updatable fields provided"}), 400
    # Map legacy statuses to canonical
    if "status" in updates:
        if updates["status"] in {"in_progress", "in-progress", "progress"}:
            updates["status"] = "doing"
        if updates["status"] in {"completed", "complete"}:
            updates["status"] = "done"

    # Log events per field
    for k, v in updates.items():
        if k == "checklist":
            try:
                import json as _json

                _val = _json.dumps(v)
            except Exception:
                _val = str(v)
            _db.add_event(task_id, k, None, _val)
        else:
            _db.add_event(
                task_id,
                k,
                str(existing.get(k)) if existing.get(k) is not None else None,
                str(v) if v is not None else None,
            )

    # Serialize checklist to JSON string for storage
    updates_to_store = dict(updates)
    if "checklist" in updates_to_store:
        try:
            import json as _json

            updates_to_store["checklist"] = _json.dumps(updates_to_store["checklist"])  # type: ignore[index]
        except Exception:
            pass
    _db.update_task_fields(task_id, updates_to_store)

    # If marking done, remove from DB+JSON now queue
    if updates.get("status") in {"done", "completed"}:
        with contextlib.suppress(Exception):
            _db.remove_from_now_queue(task_id)
        # Also update JSON now_queue
        now_queue_file = STATE_DIR / "now_queue.json"
        if now_queue_file.exists():
            try:
                with open(now_queue_file) as f:
                    now_payload = json.load(f)
                now_payload["queue"] = [
                    t for t in now_payload.get("queue", []) if t.get("id") != task_id
                ]
                now_payload.setdefault("metadata", {})["updated"] = datetime.now().isoformat()
                with open(now_queue_file, "w") as f:
                    json.dump(now_payload, f, indent=2)
            except Exception:
                pass

    # Export tasks snapshot
    _db.export_snapshot_to_json(TASKS_FILE)

    task = _db.get_task(task_id)
    return jsonify({"success": True, "task": task})


@app.route("/api/stats", methods=["GET"])
def api_stats() -> ResponseReturnValue:
    """Return basic task statistics derived from DB."""
    tasks = _db.list_tasks()
    if app.config.get("TESTING") and not tasks:
        # In tests, allow reading legacy JSON if DB empty
        tasks = _legacy_tasks_from_json()
    total = len(tasks)
    statuses = [str(t.get("status")) for t in tasks]
    todo = statuses.count("todo")
    doing = statuses.count("doing") + statuses.count("in_progress")
    review = statuses.count("review")
    done = statuses.count("done") + statuses.count("completed")
    blocked = sum(1 for t in tasks if t.get("status") == "blocked")
    return jsonify(
        {
            "total": total,
            "todo": todo,
            "doing": doing,
            "review": review,
            "done": done,
            "blocked": blocked,
            # Back-compat fields
            "completed": done,
            "in_progress": doing,
        }
    )


@app.route("/api/tasks/bulk-update", methods=["POST"])
def api_bulk_update() -> ResponseReturnValue:
    """DB-backed bulk update by equality filter.

    Expected: {"filter": {...}, "update": {...}}
    """
    body = request.get_json(silent=True) or {}
    if "filter" not in body or "update" not in body:
        return jsonify({"error": "Missing filter or update parameters"}), 400

    filt = body["filter"] or {}
    update_params = body["update"] or {}
    # Map legacy statuses to canonical
    if "status" in update_params:
        if update_params["status"] in {"in_progress", "in-progress", "progress"}:
            update_params["status"] = "doing"
        if update_params["status"] in {"completed", "complete"}:
            update_params["status"] = "done"

    tasks = _db.list_tasks()
    target_ids = [t["id"] for t in tasks if all(t.get(k) == v for k, v in filt.items())]

    updated_count = 0
    for tid in target_ids:
        existing = _db.get_task(tid)
        if not existing:
            continue
        # Log events
        for k, v in update_params.items():
            _db.add_event(
                tid,
                k,
                str(existing.get(k)) if existing.get(k) is not None else None,
                str(v) if v is not None else None,
            )
        if _db.update_task_fields(tid, update_params):
            updated_count += 1

    # Snapshot export for UI
    if updated_count:
        try:
            with open(TASKS_FILE, "w") as f:
                json.dump(_db.export_tasks_json(), f, indent=2)
        except Exception:
            pass

    return jsonify({"success": True, "updated_count": updated_count})


@app.route("/api/export", methods=["GET"])
def api_export() -> ResponseReturnValue:
    """Export tasks in CSV, JSON, or ICS format.

    Query params: format=csv|json|ics, optional course, status filters.
    """
    export_format = (request.args.get("format", "csv") or "csv").lower()
    course = request.args.get("course")
    status = request.args.get("status")

    tasks = _db.list_tasks(status=status, course=course)

    if export_format == "json":
        payload = {
            "exported_at": datetime.now().isoformat(),
            "filters": {"course": course, "status": status},
            "count": len(tasks),
            "tasks": tasks,
        }
        return Response(
            json.dumps(payload, indent=2),
            mimetype="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=tasks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            },
        )

    if export_format == "csv":
        import csv
        from io import StringIO

        output = StringIO()
        fieldnames = [
            "id",
            "course",
            "title",
            "status",
            "priority",
            "category",
            "due_date",
            "description",
            "created_at",
            "updated_at",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for task in tasks:
            row = {k: task.get(k) for k in fieldnames}
            # Map canonical status to legacy names for CSV
            if row.get("status") == "doing":
                row["status"] = "in_progress"
            if row.get("status") == "done":
                row["status"] = "completed"
            # Map due_at to due_date if needed
            if not row.get("due_date") and task.get("due_at"):
                row["due_date"] = task.get("due_at")
            # Map notes to description
            if not row.get("description") and task.get("notes"):
                row["description"] = task.get("notes")
            writer.writerow(row)

        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=tasks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            },
        )

    if export_format == "ics":

        def _priority_to_ics(priority: str) -> int:
            mapping = {"critical": 1, "high": 3, "medium": 5, "low": 7}
            return mapping.get(priority, 5)

        def _status_to_ics(status_value: str) -> str:
            mapping = {
                "todo": "NEEDS-ACTION",
                "in_progress": "IN-PROCESS",
                "completed": "COMPLETED",
                "blocked": "CANCELLED",
                "deferred": "TENTATIVE",
            }
            return mapping.get(status_value, "NEEDS-ACTION")

        ics_lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Dashboard//Task Calendar//EN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
        ]

        from datetime import datetime as _dt

        for task in tasks:
            # Accept due_date or due_at (date-only or ISO timestamp)
            dstr = task.get("due_date") or task.get("due_at") or ""
            due = ""
            if dstr:
                try:
                    # Try ISO parse and convert to date-only
                    due = _dt.fromisoformat(dstr).strftime("%Y%m%d")
                except Exception:
                    # Fallback: use first 10 chars if looks like YYYY-MM-DD
                    if len(dstr) >= 10 and dstr[4] == "-" and dstr[7] == "-":
                        due = dstr[:10].replace("-", "")
            if len(due) == 8:  # YYYYMMDD
                ics_lines.extend(
                    [
                        "BEGIN:VEVENT",
                        f"UID:{task.get('id')}@dashboard.local",
                        f"DTSTART;VALUE=DATE:{due}",
                        f"DTEND;VALUE=DATE:{due}",
                        f"SUMMARY:[{task.get('course')}] {task.get('title')}",
                        f"DESCRIPTION:{task.get('description', '')}",
                        f"PRIORITY:{_priority_to_ics(task.get('priority', 'medium'))}",
                        f"STATUS:{_status_to_ics(task.get('status', 'todo'))}",
                        "END:VEVENT",
                    ]
                )

        ics_lines.append("END:VCALENDAR")

        return Response(
            "\r\n".join(ics_lines),
            mimetype="text/calendar",
            headers={
                "Content-Disposition": f"attachment; filename=tasks_{datetime.now().strftime('%Y%m%d')}.ics"
            },
        )

    return jsonify({"error": f"Unsupported format: {export_format}"}), 400


@app.route("/api/task/<task_id>", methods=["GET", "POST"])
def api_task(task_id: str) -> ResponseReturnValue:
    """DB-backed task operations: GET returns task, POST updates fields with events."""
    if request.method == "GET":
        t = _db.get_task(task_id)
        if not t:
            return jsonify({"error": "Task not found"}), 404
        return jsonify({"task": t})

    # POST: update status/fields
    body = request.get_json(silent=True) or {}
    existing = _db.get_task(task_id)
    if not existing:
        return jsonify({"error": "Task not found"}), 404

    allowed = {"status", "notes", "title", "due_at", "est_minutes", "weight", "category"}
    updates = {k: v for k, v in body.items() if k in allowed}
    if not updates:
        return jsonify({"error": "No updatable fields provided"}), 400
    # Map legacy statuses to canonical
    if "status" in updates:
        if updates["status"] in {"in_progress", "in-progress", "progress"}:
            updates["status"] = "doing"
        if updates["status"] in {"completed", "complete"}:
            updates["status"] = "done"

    # Log events
    for k, v in updates.items():
        _db.add_event(
            task_id,
            k,
            str(existing.get(k)) if existing.get(k) is not None else None,
            str(v) if v is not None else None,
        )

    _db.update_task_fields(task_id, updates)

    # If completed, remove from queue both DB and JSON
    if updates.get("status") in {"done", "completed"}:
        with contextlib.suppress(Exception):
            _db.remove_from_now_queue(task_id)
        now_queue_file = STATE_DIR / "now_queue.json"
        if now_queue_file.exists():
            try:
                with open(now_queue_file) as f:
                    now_payload = json.load(f)
                now_payload["queue"] = [
                    t for t in now_payload.get("queue", []) if t.get("id") != task_id
                ]
                now_payload.setdefault("metadata", {})["updated"] = datetime.now().isoformat()
                with open(now_queue_file, "w") as f:
                    json.dump(now_payload, f, indent=2)
            except Exception:
                pass

    # Export tasks snapshot for UI
    _db.export_snapshot_to_json(TASKS_FILE)

    updated = _db.get_task(task_id)
    return jsonify({"success": True, "task": updated})


@app.route("/api/tasks/bulk", methods=["POST"])
def api_bulk_update_tasks_list() -> ResponseReturnValue:
    """DB-backed bulk update with an explicit list: {"tasks":[{id, field:value,...}]}"""
    body = request.get_json(silent=True) or {}
    items = body.get("tasks") or []
    if not isinstance(items, list) or not items:
        return jsonify({"error": "Provide tasks list"}), 400

    updated_count = 0
    for upd in items:
        tid = upd.get("id")
        if not tid:
            continue
        existing = _db.get_task(tid)
        if not existing:
            continue
        updates = {k: v for k, v in upd.items() if k != "id"}
        if not updates:
            continue
        for k, v in updates.items():
            _db.add_event(
                tid,
                k,
                str(existing.get(k)) if existing.get(k) is not None else None,
                str(v) if v is not None else None,
            )
        if _db.update_task_fields(tid, updates):
            updated_count += 1

    # Snapshot export
    _db.export_snapshot_to_json(TASKS_FILE)
    return jsonify({"success": True, "updated": updated_count})


@app.route("/view/<view_name>")
def filtered_view(view_name: str) -> str:
    """Filtered views (today, week, overdue, etc.)."""
    tasks = _db.list_tasks()
    filtered_tasks: list[dict[str, Any]] = []
    now = datetime.now()

    if view_name == "today":
        for task in tasks:
            d = task.get("due_at") or task.get("due_date")
            if d:
                try:
                    due = datetime.fromisoformat(d)
                    if due.date() == now.date():
                        filtered_tasks.append(task)
                except (ValueError, TypeError, AttributeError) as e:
                    logger.debug(f"Invalid date in filtered view: {e}")
                    continue

    elif view_name == "week":
        week_end = now + timedelta(days=7)
        for task in tasks:
            d = task.get("due_at") or task.get("due_date")
            if d:
                try:
                    due = datetime.fromisoformat(d)
                    if now <= due <= week_end:
                        filtered_tasks.append(task)
                except (ValueError, TypeError, AttributeError) as e:
                    logger.debug(f"Invalid date in filtered view: {e}")
                    continue

    elif view_name == "overdue":
        for task in tasks:
            d = task.get("due_at") or task.get("due_date")
            if d and task.get("status") not in {"done", "completed"}:
                try:
                    due = datetime.fromisoformat(d)
                    if due < now:
                        filtered_tasks.append(task)
                except (ValueError, TypeError, AttributeError) as e:
                    logger.debug(f"Invalid date in filtered view: {e}")
                    continue

    elif view_name == "blocked":
        filtered_tasks = [t for t in tasks if t.get("status") == "blocked"]

    elif view_name == "doing":
        filtered_tasks = [t for t in tasks if t.get("status") == "doing"]

    # Add display helpers
    for task in filtered_tasks:
        task["priority"] = calculate_priority(task)
        task["status_color"] = get_status_color(task.get("status", "todo"))
        task["due_color"] = get_due_color(task)

        if "due" in task:
            try:
                due = datetime.fromisoformat(task["due"])
                task["due_display"] = due.strftime("%b %d, %Y")
                task["due_relative"] = get_relative_time(due)
            except (ValueError, TypeError, AttributeError) as e:
                logger.debug(f"Failed to format due date for task {task.get('id')}: {e}")
                task["due_display"] = task["due"]

    filtered_tasks.sort(key=lambda t: t["priority"], reverse=True)

    return cast(
        str,
        render_template(
            "filtered.html",
            tasks=filtered_tasks,
            view_name=view_name.title(),
            count=len(filtered_tasks),
        ),
    )


def get_relative_time(dt: datetime) -> str:
    """Get human-readable relative time."""
    now = datetime.now()
    if dt.tzinfo is None:
        dt = TIMEZONE.localize(dt)
    if now.tzinfo is None:
        now = TIMEZONE.localize(now)

    diff = dt - now
    days = diff.days

    if days < -1:
        return f"{-days} days overdue"
    elif days == -1:
        return "1 day overdue"
    elif days == 0:
        return "Due today"
    elif days == 1:
        return "Due tomorrow"
    elif days <= 7:
        return f"Due in {days} days"
    else:
        return f"Due in {days} days"


@app.route("/preview")
def syllabus_preview() -> str:
    """Enhanced syllabus preview page."""
    courses = load_courses().get("courses", [])
    return render_template("syllabus_preview.html", courses=courses)  # type: ignore[no-any-return]


@app.route("/syllabi")
def syllabi_listing() -> str:
    """V2 Architecture: List all available syllabi."""
    syllabi_dir = Path(Config.BUILD_DIR) / "syllabi"
    syllabi = []

    if syllabi_dir.exists():
        for syllabus_file in sorted(syllabi_dir.glob("*.html")):
            # Skip calendar versions
            if "_with_calendar" not in syllabus_file.name:
                course_code = syllabus_file.stem
                syllabi.append(
                    {
                        "code": course_code,
                        "name": get_course_name(course_code),
                        "url": f"/syllabi/{course_code}",
                        "with_calendar_url": f"/syllabi/{course_code}_with_calendar",
                    }
                )

    return render_template("syllabi_listing.html", syllabi=syllabi)  # type: ignore[no-any-return]


@app.route("/schedules")
def schedules_listing() -> str:
    """V2 Architecture: List all available schedules."""
    schedules_dir = Path(Config.BUILD_DIR) / "schedules"
    schedules = []

    if schedules_dir.exists():
        for schedule_file in sorted(schedules_dir.glob("*_schedule.html")):
            course_code = schedule_file.stem.replace("_schedule", "")
            schedules.append(
                {
                    "code": course_code,
                    "name": get_course_name(course_code),
                    "url": f"/schedules/{course_code}",
                    "embed_url": f"/embed/schedule/{course_code}",
                }
            )

    return render_template("schedules_listing.html", schedules=schedules)  # type: ignore[no-any-return]


def get_course_name(course_code: str) -> str:
    """Get course name from course code."""
    course_names = {
        "MATH221": "Applied Calculus",
        "MATH251": "Calculus I",
        "STAT253": "Applied Statistics",
    }
    return course_names.get(course_code, course_code)


@app.route("/api/schedule/<course_code>")
def get_schedule_html(course_code: str) -> ResponseReturnValue:
    """Get schedule as HTML for preview."""
    import markdown as md  # type: ignore[import-untyped]

    schedule_dir = Config.BUILD_DIR / "schedules"
    schedule_path = schedule_dir / f"{course_code}_schedule.md"

    if not schedule_path.exists():
        return jsonify({"error": "Schedule not found"}), 404

    # Read and convert markdown to HTML
    with open(schedule_path) as f:
        markdown_content = f.read()

    # Convert to HTML with tables extension
    html_content = md.markdown(markdown_content, extensions=["tables", "fenced_code", "nl2br"])

    # Wrap in Bootstrap-styled container
    styled_html = f"""
    <div class="container-fluid p-4">
        <style>
            table {{
                width: 100%;
                margin: 1rem 0;
            }}
            table, th, td {{
                border: 1px solid #dee2e6;
                border-collapse: collapse;
            }}
            th, td {{
                padding: 0.75rem;
                text-align: left;
            }}
            th {{
                background-color: #f8f9fa;
                font-weight: 600;
            }}
            tr:hover {{
                background-color: #f8f9fa;
            }}
            h1, h2, h3 {{
                color: #495057;
                margin-top: 1.5rem;
                margin-bottom: 1rem;
            }}
            ul, ol {{
                margin-left: 1.5rem;
            }}
            code {{
                background: #f8f9fa;
                padding: 0.2rem 0.4rem;
                border-radius: 3px;
            }}
        </style>
        {html_content}
    </div>
    """

    return styled_html


@app.route("/api/schedule/build/<course_code>", methods=["POST"])
def build_schedule(course_code: str) -> ResponseReturnValue:
    """Build schedule for a course."""
    from scripts.build_schedules import ScheduleBuilder

    try:
        builder = ScheduleBuilder(output_dir="build/schedules")
        schedule_path = builder.build_schedule(course_code)
        return jsonify({"success": True, "path": str(schedule_path)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/syllabus/pdf/<course_code>")
@app.route("/api/syllabus/pdf/<course_code>_with_calendar")
def download_syllabus_pdf(course_code: str) -> ResponseReturnValue:
    """Download syllabus as PDF."""
    from flask import abort, send_file

    # Determine if with_calendar variant is requested
    variant = "_with_calendar" if request.path.endswith("_with_calendar") else ""
    course_code = course_code.replace("_with_calendar", "")

    # Check if PDF exists
    pdf_dir = Config.BUILD_DIR / "syllabi" / "pdf"
    pdf_path = pdf_dir / f"{course_code}{variant}.pdf"

    if not pdf_path.exists():
        # Try to generate it
        try:
            from scripts.build_syllabi import SyllabusBuilder

            builder = SyllabusBuilder()
            builder.build_syllabus(course_code)
        except Exception as e:
            abort(404, f"PDF not available: {e}")

    if pdf_path.exists():
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=f"{course_code}_syllabus{variant}.pdf",
            mimetype="application/pdf",
        )
    else:
        abort(404, "PDF not found")


@app.route("/css/<path:filename>")
def serve_css(filename: str) -> ResponseReturnValue:
    """Serve CSS files from build/css directory using Flask's send_from_directory."""
    css_directory = Config.BUILD_DIR / "css"
    try:
        return send_from_directory(css_directory, filename, mimetype="text/css")
    except FileNotFoundError:
        return "CSS file not found", 404


@app.route("/schedules/<course_code>")
def view_schedule(course_code: str) -> ResponseReturnValue:
    """Serve HTML schedule for a course."""
    schedule_file = Path(Config.BUILD_DIR) / "schedules" / f"{course_code}_schedule.html"

    if not schedule_file.exists():
        # Try to build it
        subprocess.run(
            [
                "python",
                "scripts/build_schedules.py",
                "--course",
                course_code,
                "--output",
                "build/schedules",
            ],
            capture_output=True,
            text=True,
        )

        if not schedule_file.exists():
            return f"Schedule not found for {course_code}", 404

    # Read and serve the HTML directly with proper headers
    with open(schedule_file, encoding="utf-8") as f:
        content = f.read()

    response = Response(content, mimetype="text/html")
    response.headers["Content-Type"] = "text/html; charset=utf-8"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.route("/syllabi/<course_code>")
def view_syllabus(course_code: str) -> ResponseReturnValue:
    """Serve generated syllabus for a course."""
    from flask import abort

    # Use configured paths
    syllabi_dir = Config.SYLLABI_DIR

    # Try HTML first, then Markdown
    variant = (request.args.get("variant") or "").strip().lower()
    base_name = f"{course_code}_with_calendar" if variant == "with_calendar" else course_code
    html_path = syllabi_dir / f"{base_name}.html"
    md_path = syllabi_dir / f"{base_name}.md"

    if html_path.exists():
        # Read and serve the HTML directly with proper headers
        with open(html_path, encoding="utf-8") as f:
            content = f.read()

        response = Response(content, mimetype="text/html")
        response.headers["Content-Type"] = "text/html; charset=utf-8"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response
    elif md_path.exists():
        # Read markdown and render it with basic HTML wrapper
        with open(md_path) as f:
            md_content = f.read()

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{course_code} Syllabus</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                body {{ padding: 20px; max-width: 900px; margin: 0 auto; }}
                pre {{ background: #f5f5f5; padding: 10px; border-radius: 5px; }}
                table {{ width: 100%; margin: 20px 0; }}
                th, td {{ padding: 8px; border: 1px solid #ddd; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="mb-3">
                <a href="/" class="btn btn-sm btn-secondary">← Back to Dashboard</a>
            </div>
            <pre>{md_content}</pre>
        </body>
        </html>
        """
        return html_content
    else:
        abort(
            404,
            f"Syllabus not found for {course_code}{' (with calendar)' if variant == 'with_calendar' else ''}",
        )


@app.template_filter("status_icon")
def status_icon(status: str) -> str:
    """Get icon for status."""
    icons = {"blocked": "🚫", "todo": "📋", "doing": "⚡", "review": "👀", "done": "✅"}
    return icons.get(status, "❓")


# Iframe hosting routes for Blackboard Ultra integration
@app.route("/embed/syllabus/<course_code>")
def embed_syllabus(course_code: str) -> str:
    """Serve syllabus optimized for iframe embedding with CORS headers."""
    syllabus_path = Path(f"build/syllabi/{course_code}.html")

    if syllabus_path.exists():
        with open(syllabus_path, encoding="utf-8") as f:
            content = f.read()

        # Add iframe-optimized styling
        iframe_style = """
        <style>
            body {
                margin: 0;
                padding: 15px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                line-height: 1.6;
            }
            .container { max-width: 100%; }
            @media print { body { padding: 0; } }
        </style>
        """

        # Insert style before </head>
        content = content.replace("</head>", f"{iframe_style}</head>")

        response = Response(content, mimetype="text/html")
        response.headers["X-Frame-Options"] = "ALLOWALL"
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Content-Security-Policy"] = "frame-ancestors *;"

        return response

    return "Syllabus not found", 404


@app.route("/embed/schedule/<course_code>")
def embed_schedule(course_code: str) -> str:
    """Serve course schedule optimized for iframe embedding - V2 architecture."""
    # V2 naming convention
    schedule_path = Path(f"build/schedules/{course_code}_schedule.html")

    if schedule_path.exists():
        with open(schedule_path, encoding="utf-8") as f:
            content = f.read()

        # Add iframe-optimized styling
        iframe_style = """
        <style>
            body {
                margin: 0;
                padding: 15px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 10px;
            }
            th, td {
                padding: 8px;
                border: 1px solid #ddd;
                text-align: left;
            }
            th {
                background-color: #f8f9fa;
                font-weight: 600;
            }
            tr:hover { background-color: #f5f5f5; }
            @media (max-width: 768px) {
                body { padding: 10px; }
                th, td { padding: 5px; font-size: 14px; }
            }
        </style>
        """

        content = content.replace("</head>", f"{iframe_style}</head>")

        response = Response(content, mimetype="text/html")
        response.headers["X-Frame-Options"] = "ALLOWALL"
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Content-Security-Policy"] = "frame-ancestors *;"

        return response

    return "Schedule not found", 404


@app.route("/embed/generator")
def embed_generator() -> str:
    """Generate iframe embed codes for Blackboard Ultra."""
    courses_data = load_courses()
    courses = [c["code"] for c in courses_data.get("courses", [])]
    if not courses:  # Fallback
        courses = ["MATH221", "MATH251", "STAT253"]

    # Use public URL for iframe generation instead of local dev server
    base_url = Config.PUBLIC_BASE_URL

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Blackboard Ultra Embed Code Generator</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            .code-block {{
                background: #f5f5f5;
                padding: 15px;
                border-radius: 5px;
                font-family: 'Courier New', monospace;
                font-size: 14px;
                margin: 10px 0;
                position: relative;
            }}
            .copy-btn {{
                position: absolute;
                top: 10px;
                right: 10px;
            }}
            .copied {{
                background-color: #28a745 !important;
                border-color: #28a745 !important;
            }}
        </style>
    </head>
    <body>
        <div class="container mt-4">
            <h1>Blackboard Ultra Embed Code Generator</h1>
            <p class="lead">Copy and paste these iframe codes into Blackboard Ultra's HTML editor</p>

            <div class="alert alert-info">
                <h5><i class="bi bi-info-circle"></i> How to Use in Blackboard Ultra</h5>
                <ol>
                    <li>In Blackboard Ultra, create a new Content Item or edit existing</li>
                    <li>Choose "Create" → "Document" or similar content type</li>
                    <li>Click the HTML source button (&lt;/&gt;) in the editor toolbar</li>
                    <li>Paste the iframe code below</li>
                    <li>Click "Save" - content will appear with proper CORS headers</li>
                    <li><strong>Note:</strong> iframes show live content from your server</li>
                </ol>
                <div class="mt-2">
                    <strong>Public URL:</strong> <code>{base_url}</code><br>
                    <small class="text-muted">iframes will load content from your production Cloudflare Pages deployment.</small>
                    <br><small class="text-warning"><i class="bi bi-exclamation-triangle"></i> Ensure content is deployed to production before using these codes!</small>
                </div>
            </div>
    """

    for course in courses:
        html += f"""
            <div class="card mb-4">
                <div class="card-header">
                    <h3>{course}</h3>
                </div>
                <div class="card-body">
                    <h5>Syllabus Embed Code:</h5>
                    <div class="code-block">
                        <button class="btn btn-sm btn-primary copy-btn" onclick="copyCode(this, 'syllabus-{course}')">Copy</button>
                        <code id="syllabus-{course}">&lt;iframe src="{base_url}/courses/{course}/fall-2025/syllabus/embed/"
    width="100%"
    height="800"
    frameborder="0"
    style="border: 1px solid #ddd; border-radius: 4px;"
    title="{course} Syllabus"&gt;&lt;/iframe&gt;</code>
                    </div>

                    <h5>Schedule Embed Code:</h5>
                    <div class="code-block">
                        <button class="btn btn-sm btn-primary copy-btn" onclick="copyCode(this, 'schedule-{course}')">Copy</button>
                        <code id="schedule-{course}">&lt;iframe src="{base_url}/courses/{course}/fall-2025/schedule/embed/"
    width="100%"
    height="600"
    frameborder="0"
    style="border: 1px solid #ddd; border-radius: 4px;"
    title="{course} Schedule"&gt;&lt;/iframe&gt;</code>
                    </div>

                    <div class="row mt-3">
                        <div class="col">
                            <a href="{base_url}/courses/{course}/fall-2025/syllabus/embed/" target="_blank" class="btn btn-outline-primary">
                                Preview Syllabus
                            </a>
                        </div>
                        <div class="col">
                            <a href="{base_url}/courses/{course}/fall-2025/schedule/embed/" target="_blank" class="btn btn-outline-primary">
                                Preview Schedule
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        """

    html += """
        </div>
        <script>
            function copyCode(btn, codeId) {
                const code = document.getElementById(codeId).textContent;
                navigator.clipboard.writeText(code).then(() => {
                    btn.textContent = 'Copied!';
                    btn.classList.add('copied');
                    setTimeout(() => {
                        btn.textContent = 'Copy';
                        btn.classList.remove('copied');
                    }, 2000);
                });
            }
        </script>
    </body>
    </html>
    """

    return html


@app.route("/api/syllabus/download/<course_code>.<format>")
def download_syllabus(course_code: str, format: str) -> ResponseReturnValue:
    """Download syllabus as HTML or DOCX."""
    import subprocess
    import tempfile

    if format not in ["html", "docx"]:
        return jsonify({"error": "Invalid format. Use 'html' or 'docx'"}), 400

    # Get variant from query parameter
    variant = request.args.get("variant", "embed")

    # Get the HTML file from site directory (production-ready version)
    if variant == "with_calendar":
        html_path = (
            Config.PROJECT_ROOT
            / "site"
            / "courses"
            / course_code
            / "fall-2025"
            / "syllabus"
            / "index.html"
        )
    else:
        html_path = (
            Config.PROJECT_ROOT
            / "site"
            / "courses"
            / course_code
            / "fall-2025"
            / "syllabus"
            / "embed"
            / "index.html"
        )

    if not html_path.exists():
        return jsonify({"error": "Syllabus HTML not found. Try rebuilding site."}), 404

    if format == "html":
        # Return the HTML file directly
        return send_file(
            html_path,
            as_attachment=True,
            download_name=f"{course_code}_syllabus_fall2025.html",
            mimetype="text/html",
        )

    elif format == "docx":
        # Convert HTML to DOCX using pandoc
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp_docx:
            try:
                # Use pandoc to convert HTML to DOCX
                cmd = ["pandoc", str(html_path), "-f", "html", "-t", "docx", "-o", tmp_docx.name]

                # Add reference doc if it exists
                ref_doc = Config.PROJECT_ROOT / "assets" / "reference.docx"
                if ref_doc.exists():
                    cmd.extend(["--reference-doc", str(ref_doc)])

                result = subprocess.run(
                    cmd, capture_output=True, text=True, cwd=Config.PROJECT_ROOT
                )

                if result.returncode != 0:
                    return jsonify({"error": f"Pandoc conversion failed: {result.stderr}"}), 500

                # Send the DOCX file
                return send_file(
                    tmp_docx.name,
                    as_attachment=True,
                    download_name=f"{course_code}_syllabus_fall2025.docx",
                    mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            finally:
                # Clean up temp file after sending
                import os

                if os.path.exists(tmp_docx.name):
                    os.unlink(tmp_docx.name)


@app.route("/api/schedule/download/<course_code>.<format>")
def download_schedule(course_code: str, format: str) -> ResponseReturnValue:
    """Download schedule as HTML or DOCX."""
    import subprocess
    import tempfile

    if format not in ["html", "docx"]:
        return jsonify({"error": "Invalid format. Use 'html' or 'docx'"}), 400

    # Build the schedule first to ensure it's up to date
    from scripts.build_schedules import ScheduleBuilder

    try:
        builder = ScheduleBuilder(output_dir="build/schedules")
        builder.build_schedule(course_code)
    except Exception as e:
        return jsonify({"error": f"Failed to build schedule: {str(e)}"}), 500

    # Get the HTML file from site directory (production-ready version)
    html_path = (
        Config.PROJECT_ROOT
        / "site"
        / "courses"
        / course_code
        / "fall-2025"
        / "schedule"
        / "index.html"
    )

    if not html_path.exists():
        # Try embed version
        html_path = (
            Config.PROJECT_ROOT
            / "site"
            / "courses"
            / course_code
            / "fall-2025"
            / "schedule"
            / "embed"
            / "index.html"
        )

    if not html_path.exists():
        return jsonify({"error": "Schedule HTML not found. Try rebuilding site."}), 404

    if format == "html":
        # Return the HTML file directly
        return send_file(
            html_path,
            as_attachment=True,
            download_name=f"{course_code}_schedule_fall2025.html",
            mimetype="text/html",
        )

    elif format == "docx":
        # Convert HTML to DOCX using pandoc
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp_docx:
            try:
                # Use pandoc to convert HTML to DOCX
                cmd = ["pandoc", str(html_path), "-f", "html", "-t", "docx", "-o", tmp_docx.name]

                # Add reference doc if it exists
                ref_doc = Config.PROJECT_ROOT / "assets" / "reference.docx"
                if ref_doc.exists():
                    cmd.extend(["--reference-doc", str(ref_doc)])

                result = subprocess.run(
                    cmd, capture_output=True, text=True, cwd=Config.PROJECT_ROOT
                )

                if result.returncode != 0:
                    return jsonify({"error": f"Pandoc conversion failed: {result.stderr}"}), 500

                # Send the DOCX file
                return send_file(
                    tmp_docx.name,
                    as_attachment=True,
                    download_name=f"{course_code}_schedule_fall2025.docx",
                    mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            finally:
                # Clean up temp file after sending
                import os

                if os.path.exists(tmp_docx.name):
                    os.unlink(tmp_docx.name)


@app.route("/api/export/docx")
def export_docx() -> ResponseReturnValue:
    """Export all syllabi and schedules as DOCX files using pandoc."""
    import subprocess
    import tempfile
    import zipfile

    try:
        # Create temporary directory for DOCX files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            zip_path = temp_path / "course_materials.zip"

            # Get course codes
            courses_data = load_courses()
            course_codes = [c["code"] for c in courses_data.get("courses", [])]

            # Create ZIP file with all DOCX exports
            with zipfile.ZipFile(zip_path, "w") as zip_file:
                for course_code in course_codes:
                    # Convert syllabus to DOCX
                    syllabus_html = Config.SYLLABI_DIR / f"{course_code}.html"
                    if syllabus_html.exists():
                        syllabus_docx = temp_path / f"{course_code}_syllabus.docx"
                        subprocess.run(
                            [
                                "pandoc",
                                str(syllabus_html),
                                "-o",
                                str(syllabus_docx),
                                "--from=html",
                                "--to=docx",
                            ],
                            check=True,
                        )
                        zip_file.write(syllabus_docx, f"{course_code}_syllabus.docx")

                    # Convert schedule to DOCX if it exists
                    schedule_html = Config.SCHEDULES_DIR / f"{course_code}.html"
                    if schedule_html.exists():
                        schedule_docx = temp_path / f"{course_code}_schedule.docx"
                        subprocess.run(
                            [
                                "pandoc",
                                str(schedule_html),
                                "-o",
                                str(schedule_docx),
                                "--from=html",
                                "--to=docx",
                            ],
                            check=True,
                        )
                        zip_file.write(schedule_docx, f"{course_code}_schedule.docx")

                # Create combined document for admin
                combined_html = temp_path / "combined.html"
                with open(combined_html, "w") as f:
                    f.write(
                        "<html><head><title>All Course Materials - Fall 2025</title></head><body>"
                    )
                    f.write("<h1>Course Materials - Fall 2025</h1>")

                    for course_code in course_codes:
                        syllabus_html = Config.SYLLABI_DIR / f"{course_code}.html"
                        schedule_html = Config.SCHEDULES_DIR / f"{course_code}.html"

                        f.write(f"<h2>{course_code}</h2>")

                        if syllabus_html.exists():
                            f.write(f"<h3>{course_code} Syllabus</h3>")
                            f.write(syllabus_html.read_text())
                            f.write("<div style='page-break-after: always;'></div>")

                        if schedule_html.exists():
                            f.write(f"<h3>{course_code} Schedule</h3>")
                            f.write(schedule_html.read_text())
                            f.write("<div style='page-break-after: always;'></div>")

                    f.write("</body></html>")

                # Convert combined document to DOCX
                combined_docx = temp_path / "combined_all_courses.docx"
                subprocess.run(
                    [
                        "pandoc",
                        str(combined_html),
                        "-o",
                        str(combined_docx),
                        "--from=html",
                        "--to=docx",
                    ],
                    check=True,
                )
                zip_file.write(combined_docx, "combined_all_courses.docx")

            return send_file(
                zip_path,
                as_attachment=True,
                download_name="course_materials_fall2025.zip",
                mimetype="application/zip",
            )

    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"Pandoc conversion failed: {e}"}), 500
    except Exception as e:
        return jsonify({"error": f"Export failed: {e}"}), 500


@app.route("/api/site/preview/start", methods=["POST"])
def start_site_preview():
    """Start the local site preview server."""
    try:
        import subprocess
        import threading

        def run_server():
            # Start the site preview server in the background
            subprocess.Popen(
                ["python", "-m", "http.server", "8000", "-d", str(Config.PROJECT_ROOT / "site")]
            )

        # Start server in a separate thread
        threading.Thread(target=run_server, daemon=True).start()

        return jsonify(
            {"success": True, "message": "Site preview server starting at http://localhost:8000"}
        )

    except Exception as e:
        logger.error(f"Error starting site preview: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/reprioritize", methods=["POST"])
def api_reprioritize() -> ResponseReturnValue:
    """Regenerate the Now Queue using DB-backed prioritization service."""
    try:
        # Refresh via service; exports JSON snapshot for UI compatibility
        _prio.refresh_now_queue(timebox=int(request.args.get("timebox", 90) or 90))
        # Report count from DB queue if available, else from snapshot
        q = _db.get_now_queue()
        count = len(q)
        if count == 0:
            now_path = STATE_DIR / "now_queue.json"
            if now_path.exists():
                try:
                    payload = json.loads(now_path.read_text())
                    count = len(payload.get("queue", []))
                except Exception:
                    pass
        return jsonify({"success": True, "message": "Now Queue regenerated", "task_count": count})
    except Exception as e:
        logger.error(f"Error during reprioritization: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/orchestrate", methods=["POST"])
def api_orchestrate() -> ResponseReturnValue:
    """Analyze and orchestrate task execution."""
    # Use DB export mapping for orchestrator
    try:
        tasks = _db.export_tasks_json().get("tasks", [])
    except Exception:
        tasks = _legacy_tasks_from_json()

    # Analyze task graph
    analysis = orchestrator.analyze_task_graph(tasks)

    # Get suggestions for next tasks
    completed = [t["id"] for t in tasks if t.get("status") == "done"]
    available = [t for t in tasks if t.get("status") in ["todo", "blocked"]]
    suggestions = orchestrator.suggest_next_tasks(completed, available)

    # Convert sets to lists for JSON serialization
    if "parallel_groups" in analysis:
        analysis["parallel_groups"] = [list(group) for group in analysis["parallel_groups"]]

    return jsonify(
        {
            "analysis": analysis,
            "suggestions": [{"task_id": tid, "confidence": score} for tid, score in suggestions],
            "agent_status": agent_coordinator.get_agent_status(),
        }
    )


@app.route("/api/agent/register", methods=["POST"])
def api_register_agent() -> ResponseReturnValue:
    """Register a new agent with capabilities."""
    body = request.get_json(silent=True) or {}
    agent_id = body.get("agent_id")
    capabilities = body.get("capabilities", [])

    if not agent_id:
        return jsonify({"error": "Missing agent_id"}), 400

    agent_coordinator.register_agent(agent_id, capabilities)

    return jsonify({"success": True, "agent_id": agent_id})


@app.route("/api/agent/assign", methods=["POST"])
def api_assign_task() -> ResponseReturnValue:
    """Assign a task to an available agent."""
    body = request.get_json(silent=True) or {}
    task_id = body.get("task_id")

    if not task_id:
        return jsonify({"error": "Missing task_id"}), 400

    # Load task data
    # Fetch from DB
    task = _db.get_task(task_id)

    if not task:
        return jsonify({"error": "Task not found"}), 404

    assigned_agent = agent_coordinator.assign_task(task)

    if assigned_agent:
        return jsonify({"success": True, "agent_id": assigned_agent})
    else:
        return jsonify({"error": "No available agent for task"}), 503


# --- New API: health, phase, explain, now_queue refresh, quick_add (skeletons) ---


@app.route("/api/health", methods=["GET"])
def api_health() -> ResponseReturnValue:
    """DB + DAG health including last scoring time."""
    return jsonify(_prio.health())


@app.route("/api/phase", methods=["GET"])
def api_phase() -> ResponseReturnValue:
    """Return current phase and weights."""
    _prio.health()
    # Use health to confirm DB works; phase computed during refresh endpoints; quick compute here:
    from dashboard.tools.phase import detect_phase, load_semester_start, phase_weights

    sem = load_semester_start(Path("academic-calendar.json"))
    if sem is None:
        return jsonify({"phase": "in_term", "weights": phase_weights("in_term")})
    key = detect_phase(sem)
    return jsonify({"phase": key, "weights": phase_weights(key)})


@app.route("/api/explain/<task_id>", methods=["GET"])
def api_explain(task_id: str) -> ResponseReturnValue:
    """Explain score for a task using DB-backed service."""
    payload = _prio.explain(task_id)
    if payload.get("error"):
        return jsonify(payload), 404
    return jsonify(payload)


@app.route("/api/now_queue/refresh", methods=["POST"])
def api_now_queue_refresh() -> ResponseReturnValue:
    """Regenerate Now Queue via service using DB + solver, export JSON."""
    args = request.args or {}
    timebox = int(args.get("timebox", 0) or 0)
    energy = (args.get("energy") or "medium").lower()
    # Simple energy mapping
    heavy_threshold = 60
    if energy == "low":
        if not timebox:
            timebox = 45
        heavy_threshold = 45
    elif energy == "high":
        if not timebox:
            timebox = 120
        heavy_threshold = 90
    if not timebox:
        timebox = 90
    courses_param = args.get("courses")
    include_courses: set[str] | None = None
    if courses_param:
        include_courses = {c.strip() for c in courses_param.split(",") if c.strip()}
    queue_ids = _prio.refresh_now_queue(
        timebox=timebox, k=3, heavy_threshold=heavy_threshold, include_courses=include_courses
    )
    return jsonify({"queue": queue_ids, "count": len(queue_ids)})


@app.route("/api/analytics/summary", methods=["GET"])
def api_analytics_summary() -> ResponseReturnValue:
    """Simple analytics summary from events: velocity and aging."""
    import datetime as _dt

    now = _dt.datetime.utcnow()
    week_ago = now - _dt.timedelta(days=7)

    # Velocity: count of status->done events in last week, and top category of these tasks
    with _db.connect() as conn:
        ev = conn.execute(
            "select task_id, at from events where field='status' and to_val='done' and at >= ?",
            (week_ago.replace(microsecond=0).isoformat() + "Z",),
        ).fetchall()
        done_ids = [r["task_id"] for r in ev]
        cats = {}
        if done_ids:
            q_marks = ",".join(["?"] * len(done_ids))
            rows = conn.execute(
                f"select category from tasks where id in ({q_marks})", done_ids
            ).fetchall()
            for r in rows:
                c = (r["category"] or "uncat").lower()
                cats[c] = cats.get(c, 0) + 1

        # Aging: tasks in todo/review with updated_at older than 7 days
        cutoff = (now - _dt.timedelta(days=7)).replace(microsecond=0).isoformat() + "Z"
        aging_rows = conn.execute(
            "select status, count(*) as n from tasks where status in ('todo','review') and updated_at < ? group by status",
            (cutoff,),
        ).fetchall()

    top_cat = max(cats.items(), key=lambda kv: kv[1])[0] if cats else None
    aging = {r["status"]: r["n"] for r in aging_rows}
    return jsonify(
        {
            "velocity": {"total": len(done_ids), "top_category": top_cat},
            "aging": {
                "todo_gt7": int(aging.get("todo", 0)),
                "review_gt7": int(aging.get("review", 0)),
            },
        }
    )


@app.route("/api/retro/weekly", methods=["GET"])
def api_retro_weekly() -> ResponseReturnValue:
    """Return latest weekly retro; generate if none exists."""
    retro_dir = Config.STATE_DIR / "retro"
    retro_dir.mkdir(exist_ok=True)
    files = sorted(retro_dir.glob("weekly_*.json"), reverse=True)
    if files:
        try:
            import json as _json

            return jsonify(_json.load(open(files[0])))
        except Exception:
            pass
    payload = generate_weekly_retro(_db, retro_dir)
    return jsonify(payload)


@app.route("/api/quick_add", methods=["POST"])
def api_quick_add() -> ResponseReturnValue:
    """Create a task from a compact payload (JSON Schema validated; optional AI structuring stub)."""
    payload = request.get_json(silent=True) or {}
    use_ai = request.args.get("use_ai") in ("1", "true", "yes") or os.environ.get(
        "LLM_ENABLED"
    ) in ("1", "true", "yes")

    # If AI toggle requested and free-text provided, do a minimal heuristic structuring
    if use_ai and "text" in payload and not payload.get("title"):
        text = str(payload.get("text") or "").strip()
        # Heuristic: [COURSE] Title (cat:category, est:minutes, due:YYYY-MM-DD)
        course = None
        if text.startswith("[") and "]" in text:
            course = text[1 : text.index("]")]
            text = text[text.index("]") + 1 :].strip()
        title = text
        import re

        cat = None
        est = None
        due = None
        m = re.search(r"cat:([a-zA-Z_]+)", text)
        if m:
            cat = m.group(1)
        m = re.search(r"est:(\d+)", text)
        if m:
            est = int(m.group(1))
        m = re.search(r"due:(\d{4}-\d{2}-\d{2})", text)
        if m:
            due = m.group(1)
        payload.setdefault("course", course)
        payload.setdefault("title", title)
        if cat:
            payload.setdefault("category", cat)
        if est:
            payload.setdefault("est_minutes", est)
        if due:
            payload.setdefault("due_at", due)

    # Validate against schema
    try:
        import json as _json

        from jsonschema import Draft202012Validator  # type: ignore

        schema_path = Config.PROJECT_ROOT / "dashboard" / "schema" / "quick_add.schema.json"
        with open(schema_path, encoding="utf-8") as _f:
            schema = _json.load(_f)
        v = Draft202012Validator(schema)
        errors = sorted(v.iter_errors(payload), key=lambda e: e.path)
        if errors:
            return jsonify(
                {
                    "error": "Schema validation failed",
                    "details": [
                        f"{'/'.join(map(str, e.path)) or '<root>'}: {e.message}" for e in errors
                    ],
                }
            ), 400
    except Exception as _val_exc:
        logger.debug("Quick add schema validation skipped: %s", _val_exc)

    title = payload.get("title")
    if not title or not isinstance(title, str) or len(title.strip()) < 3:
        return jsonify({"error": "Field 'title' is required and must be ≥3 chars"}), 400

    # Create in DB
    new_task_fields = {
        "id": payload.get("id"),
        "course": payload.get("course"),
        "title": title.strip(),
        "status": payload.get("status") or "todo",
        "category": payload.get("category"),
        "due_at": payload.get("due_at"),
        "est_minutes": payload.get("est_minutes"),
        "notes": payload.get("notes"),
        "weight": payload.get("weight", 1.0),
    }
    task_id = _db.create_task(new_task_fields)
    # Add deps if provided
    try:
        deps = payload.get("depends_on") or []
        if deps:
            _db.add_deps(task_id, deps)
    except Exception:
        pass
    _db.add_event(task_id, "create", None, "created")
    with contextlib.suppress(Exception):
        _db.add_event(task_id, "source", None, "quick_add")

    # Export snapshot
    try:
        with open(TASKS_FILE, "w") as f:
            json.dump(_db.export_tasks_json(), f, indent=2)
    except Exception:
        pass

    created = _db.get_task(task_id)
    return jsonify({"success": True, "task": created}), 201


if __name__ == "__main__":
    port = int(os.environ.get("DASH_PORT", 5055))
    host = os.environ.get("DASH_HOST", "127.0.0.1")
    debug_mode = os.environ.get("FLASK_ENV", "development") == "development"
    app.run(host=host, port=port, debug=debug_mode)
