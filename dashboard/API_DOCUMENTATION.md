# Dashboard API Documentation

## Overview

The Course Setup Dashboard provides a Flask-based web interface for managing semester preparation tasks. It integrates with the syllabus generation system to provide direct access to generated course materials.

## Architecture

### Core Components

```
dashboard/
├── app.py              # Main Flask application and routes
├── config.py           # Configuration management with env vars
├── models.py           # Task and TaskGraph data models
├── services/           # Business logic services
│   ├── task_service.py      # Task CRUD operations
│   └── dependency_service.py # Task dependency management
├── api/                # REST API endpoints
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
**Description:** Main dashboard interface  
**Response:** HTML dashboard with task lists organized by course

#### GET /syllabi/<course_code>
**Description:** Serve generated syllabus for a course  
**Parameters:**
- `course_code` (string): Course identifier (e.g., MATH221)

**Response:** 
- HTML syllabus if available
- Markdown wrapped in HTML if only .md exists
- 404 if syllabus not found

### Task Management API

#### GET /api/tasks
**Description:** Retrieve all tasks or filtered subset  
**Query Parameters:**
- `course` (string): Filter by course code
- `status` (string): Filter by status (todo, doing, done, etc.)
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

**Response:**
```json
{
  "success": true,
  "task": { /* updated task object */ }
}
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

### TaskManager Class

Central class for task data management with file locking support.

```python
class TaskManager:
    @staticmethod
    def load_tasks() -> dict[str, Any]:
        """Load tasks with file locking for concurrent access."""
        
    @staticmethod
    def save_tasks(data: dict[str, Any]) -> None:
        """Save tasks with atomic write and optional git snapshot."""
        
    @staticmethod
    def update_task_status(task_id: str, status: str) -> bool:
        """Update specific task status."""
        
    @staticmethod
    def load_courses() -> dict[str, Any]:
        """Load course configuration from state."""
```

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
Tasks are persisted in JSON format:
- Location: `dashboard/state/tasks.json`
- File locking prevents corruption
- Optional git snapshots for history

### Environment Configuration
Uses python-dotenv for configuration:
- Reads from `.env` file if present
- Falls back to system environment
- Sensible defaults for all settings

## Error Handling

### Common Issues

1. **Module Import Errors**
   - Ensure running from project root
   - Use `uv run python dashboard/app.py`

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
# From project root
uv run python dashboard/app.py

# Or using make
make dash
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
1. `TaskManager.validate_task_data()`
2. Template display logic
3. API documentation

## Security Considerations

- File locking prevents race conditions
- Input validation on all endpoints
- XSS protection via Jinja2 auto-escaping
- CSRF protection can be enabled in production
- No direct SQL - JSON file storage only

## Performance

- Tasks cached in memory during request
- File locking minimal overhead
- Bootstrap CDN for fast CSS delivery
- Minimal JavaScript for interactivity
- HTMX for partial page updates

## Future Enhancements

1. **WebSocket Support**
   - Real-time task updates
   - Collaborative editing

2. **Database Backend**
   - SQLite for better querying
   - Migration from JSON storage

3. **Authentication**
   - User accounts
   - Role-based access

4. **Advanced Filtering**
   - Complex query builder
   - Saved filter sets

5. **Export Features**
   - CSV/Excel export
   - PDF reports
   - Calendar integration
