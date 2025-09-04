# Dashboard API Documentation

## Overview

The Course Setup Dashboard provides a Flask-based web interface for managing semester preparation tasks. It integrates with the syllabus generation system to provide direct access to generated course materials.

## Architecture

### Core Components

```
dashboard/
├── app.py              # Main Flask application and routes
├── config.py           # Configuration management with env vars
├── db/
│   └── repo.py         # SQLite repository (DB-first)
├── services/           # Business logic services
│   └── dependency_service.py # Task dependency management
├── api/                # REST API endpoints (DB-backed)
│   ├── tasks.py            # Task management endpoints
│   ├── stats.py            # Statistics endpoints
│   └── tasks_htmx.py       # HTMX partial responses
└── templates/          # Jinja2 HTML templates
```

## Configuration

### Environment Variables

The dashboard uses environment variables with sensible defaults:

```bash
# Project paths (auto-detected)
PROJECT_ROOT            # Project root directory
BUILD_DIR              # Build output directory (default: build)
SYLLABI_DIR            # Syllabi directory (default: build/syllabi)
DASHBOARD_STATE_DIR    # State persistence (default: dashboard/state)

# Dashboard settings
DASH_PORT=5055         # Server port
DASH_HOST=127.0.0.1    # Server host
DASH_AUTO_SNAPSHOT=true # Git auto-snapshot on changes

# Timezone
TIMEZONE=America/Anchorage
```

### Config Class

```python
from dashboard.config import Config

# Access configuration
Config.PROJECT_ROOT    # Path object to project root
Config.SYLLABI_DIR     # Path to syllabi directory
Config.STATE_DIR       # Path to state directory
Config.AUTO_SNAPSHOT   # Boolean for auto-snapshot
```

## API Endpoints

### Main Routes

#### GET /

**Description:** Main dashboard interface with smart prioritization
**Response:** HTML dashboard featuring:

- Now Queue with 3-7 highest priority tasks
- Task lists organized by course
- Smart scores and chain head indicators
- Unblock counts showing task impact

**Features:**

- Automatically loads `now_queue.json` if available
- Displays tasks sorted by `smart_score` when present
- Falls back to basic priority calculation if not prioritized

#### GET /syllabi/<course_code>

**Description:** Serve generated syllabus for a course
**Parameters:**

- `course_code` (string): Course identifier (e.g., MATH221)

**Response:**

- HTML syllabus if available
- Markdown wrapped in HTML if only .md exists
- 404 if syllabus not found

### Task Management API (DB-backed)

#### GET /api/tasks

**Description:** Retrieve all tasks or filtered subset
**Query Parameters:**

- `course` (string): Filter by course code
- `status` (string): Filter by status. Canonical set: `todo`, `doing`, `review`, `done`, `blocked`. Legacy aliases accepted and mapped: `in_progress` -> `doing`, `completed` -> `done`.
- `priority` (string): Filter by priority level

**Response:**

```json
{
  "tasks": [
    {
      "id": "task-001",
      "course": "MATH221",
      "title": "Create syllabus",
      "status": "todo",
      "priority": "high",
      "due_date": "2025-08-20",
      "description": "Draft and finalize course syllabus"
    }
  ],
  "metadata": {
    "version": "1.0",
    "updated": "2025-08-21T23:00:00"
  }
}
```

#### POST /api/tasks

Create a new task.

Request:

```json
{
  "course": "MATH221",
  "title": "Create syllabus",
  "status": "todo",
  "priority": "high",
  "category": "setup"
}
```

Response (created task object from DB):

```json
{ "id": "MATH221-001" }
```

Example:

```bash
curl -X POST http://127.0.0.1:5055/api/tasks \
  -H 'Content-Type: application/json' \
  -d '{"course":"MATH221","title":"Create syllabus","status":"todo","priority":"high","category":"setup"}'
```

#### PUT /api/tasks/<task_id>

**Description:** Update task status or properties
**Parameters:**

- `task_id` (string): Task identifier

**Request Body:**

```json
{
  "status": "completed",
  "notes": "Optional update notes"
}
```

Response includes success and the updated task object:

```json
{ "success": true, "task": { /* ... */ } }
```

#### POST /api/tasks/bulk-update

Bulk update tasks matching a simple filter.

Request:

```json
{
  "filter": { "course": "MATH221", "status": "todo" },
  "update": { "status": "in_progress" }
}
```

Response:

```json
{ "success": true, "updated_count": 3 }
```

### Statistics API

#### GET /api/stats

**Description:** Get task statistics
**Response:**

```json
{
  "total": 15,
  "completed": 5,
  "in_progress": 3,
  "todo": 6,
  "blocked": 1,
  "overdue": 2,
  "completion_rate": 33.3,
  "by_course": {
    "MATH221": 5,
    "MATH251": 5,
    "STAT253": 5
  }
}
```

### Filtered Views

#### GET /view/<view_name>

**Description:** Pre-filtered task views
**Available Views:**

- `today` - Tasks due today
- `week` - Tasks due this week
- `overdue` - Overdue tasks
- `blocked` - Blocked tasks
- `doing` - In-progress tasks

## Data Models

### Repository Layer (DB)

The dashboard uses a SQLite repository for persistence. See `dashboard/db/repo.py`.

```python
from pathlib import Path
from dashboard.db.repo import Database, DatabaseConfig

db = Database(DatabaseConfig(Path("dashboard/state/tasks.db")))
db.initialize()

# CRUD
tid = db.create_task({"id": "MATH221-001", "title": "Create syllabus", "status": "todo"})
task = db.get_task(tid)
db.update_task_fields(tid, {"status": "doing"})
db.delete_task(tid)

# Import/Export compatibility
db.import_tasks_json(Path("dashboard/state/tasks.json"))   # optional bootstrap
payload = db.export_tasks_json()                            # JSON-compatible snapshot
```

### Prioritization & Analytics API

- GET `/api/health`: Returns repository health, DAG cycle status (`dag_ok`), `cycle_path`, `break_suggestion`, and `last_scoring` timestamp.
- GET `/api/phase`: Returns current phase key and category weights used for scoring.
- GET `/api/explain/<task_id>`: Returns score, per-factor contributions, and minimal unblocking cut for a task.
- POST `/api/now_queue/refresh?timebox=90&energy=medium&courses=MATH221,MATH251`: Recomputes Now Queue using solver/fallback and exports `dashboard/state/now_queue.json`.
- GET `/api/analytics/summary`: Velocity (last-week completions) and aging counts.
- GET `/api/retro/weekly`: Weekly retro summary (generated if absent).
- POST `/api/quick_add` (optional `?use_ai=1`): Create a task from a compact payload, validated by `dashboard/schema/quick_add.schema.json`.

Feature flags and config:
- `PRIO_USE_CPSAT=0` disables CP-SAT even if OR-Tools is installed (fallback selection used).

### Task Structure

```python
{
    "id": str,              # Unique identifier
    "course": str,          # Course code (MATH221, etc.)
    "title": str,           # Task title
    "description": str,     # Detailed description
    "status": str,          # blocked|todo|doing|review|done
    "priority": str,        # low|medium|high|critical
    "due_date": str,        # ISO format date
    "category": str,        # setup|content|technical|grading
    "depends_on": list,     # Task IDs this depends on
    "checklist": list,      # Sub-tasks checklist
    "tags": list,           # Additional tags
    "created": str,         # ISO timestamp
    "updated": str,         # ISO timestamp
}
```

## Template System

### Base Template

All pages extend `base.html` which provides:

- Bootstrap 5.1.3 CSS framework
- Responsive navigation
- Common JavaScript utilities

### Dashboard Template

`dashboard.html` displays:

- Statistics sidebar with task counts
- Course-organized task cards
- Quick filter pills
- Syllabus links per course
- Interactive status updates

### HTMX Partials

For dynamic updates without full page refresh:

- `_task_row.html` - Individual task row
- `_task_list.html` - Task list container
- `_kanban_card.html` - Kanban board card
- `_kanban_board.html` - Full kanban view

## Integration Points

### Syllabus Generation

The dashboard directly serves syllabi generated by the build system:

- HTML syllabi from `build/syllabi/*.html`
- Markdown fallback from `build/syllabi/*.md`
- Links in sidebar and course headers

### State Persistence

Tasks are persisted in SQLite (DB-first):

- Database: `dashboard/state/tasks.db` (WAL enabled, busy_timeout configured)
- Compatibility: JSON import/export supported for migration and snapshots
- Snapshots: API may export a JSON snapshot for external tools

### Environment Configuration

Uses python-dotenv for configuration:

- Reads from `.env` file if present
- Falls back to system environment
- Sensible defaults for all settings

## Error Handling

### Common Issues

1. **Module Import Errors**
   - Ensure running from project root
   - Use `BUILD_MODE=v2 uv run python -m dashboard.app`

2. **Missing Syllabi**
   - Generate with `make syllabi`
   - Check `build/syllabi/` directory

3. **State File Issues**
   - Directory created automatically
   - Check write permissions

4. **Port Already in Use**
   - Change port with `DASH_PORT=5056`
   - Kill existing process

## Development

### Running the Dashboard

```bash
# From project root (prefer module form)
BUILD_MODE=v2 DASH_PORT=5055 uv run python -m dashboard.app

# Or using make
BUILD_MODE=v2 make dash
```

### Adding New Routes

```python
@app.route("/new-endpoint")
def new_endpoint():
    """Endpoint description for API docs."""
    # Implementation
    return jsonify({"status": "success"})
```

### Extending Task Model

Add fields to task structure and update:

1. API validation helper (see `dashboard/app.py`)
2. Repository schema in `dashboard/db/repo.py` (DDL + accessors)
3. Template display logic
4. API documentation

## Security Considerations

- SQLite with WAL + busy timeout for safe local writes
- Input validation on all endpoints
- XSS protection via Jinja2 auto-escaping
- CSRF protection can be enabled in production
- Sanitized HTML output and strict content types

## Performance

- Lightweight SQLite queries with indices on common filters
- WAL journal mode minimizes write contention
- Bootstrap CDN for fast CSS delivery
- Minimal JavaScript for interactivity
- HTMX for partial page updates

## Future Enhancements

1. **WebSocket Support**
   - Real-time task updates
   - Collaborative editing

2. **Authentication**
   - User accounts
   - Role-based access

3. **Advanced Filtering**
   - Complex query builder
   - Saved filter sets

4. **Search**
   - FTS-backed search over titles/notes

## Export API

#### GET /api/export

Export tasks in various formats.

Query parameters:

- `format`: `csv` | `json` | `ics` (default: `csv`)
- `course` (optional): filter by course code
- `status` (optional): filter by task status

Examples:

```bash
# JSON export
curl 'http://127.0.0.1:5055/api/export?format=json&course=MATH221'

# CSV export
curl -OJ 'http://127.0.0.1:5055/api/export?format=csv'

# ICS export (calendar)
curl -OJ 'http://127.0.0.1:5055/api/export?format=ics'
```

The ICS export emits a VCALENDAR with a VEVENT for each task having a `due_date`.
