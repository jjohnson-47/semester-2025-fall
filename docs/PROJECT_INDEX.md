# Project Documentation Index

## Overview Documents

- **[README.md](../README.md)** - Main project overview and quick start guide
- **[AGENTS.md](../AGENTS.md)** - AI agent instructions and project context
- **[Makefile](../Makefile)** - Build automation commands

## Core Documentation

### System Architecture

- **[docs/SMART_PRIORITIZATION.md](SMART_PRIORITIZATION.md)** - Smart task prioritization system
- **[docs/TASK_TEMPLATES.md](TASK_TEMPLATES.md)** - Task template system documentation
- **[dashboard/API_DOCUMENTATION.md](../dashboard/API_DOCUMENTATION.md)** - Dashboard API reference
- **[docs/CONTENT.md](CONTENT.md)** - Content structure and organization

### Development Guides

- **[docs/FLASK_SETUP_PLAN.md](FLASK_SETUP_PLAN.md)** - Flask application setup
- **[docs/UV_MIGRATION_PLAN.md](UV_MIGRATION_PLAN.md)** - UV package manager migration
- **[docs/UV_TECHNICAL_PLAN.md](UV_TECHNICAL_PLAN.md)** - UV technical implementation
- **[docs/MYPY_STRATEGY.md](MYPY_STRATEGY.md)** - Type checking strategy

### Reference Materials

- **[docs/reference/dashboard.md](reference/dashboard.md)** - Dashboard workflow guide
- **[docs/reference/fall-2025-courses.md](reference/fall-2025-courses.md)** - Course information
- **[docs/reference/syllabus-info.md](reference/syllabus-info.md)** - Syllabus generation guide

## Key Components

### Dashboard System

```
dashboard/
├── app.py                    # Main Flask application
├── models.py                 # Task and TaskGraph models
├── config.py                 # Environment configuration
├── tools/
│   ├── reprioritize.py      # Smart prioritization engine
│   ├── priority_contracts.yaml # Prioritization strategy
│   └── generate_tasks.py    # Task generation from templates
└── state/
    ├── tasks.json           # Task database
    ├── courses.json         # Course configuration
    └── now_queue.json       # Current priority queue
```

### Content Management

```
content/courses/
├── MATH221/                 # Applied Calculus
├── MATH251/                 # Calculus I
└── STAT253/                 # Introduction to Statistics
    ├── course_description.json
    ├── course_meta.json
    ├── evaluation_tools.json
    ├── grading_policy.json
    └── [other course data files]
```

### Build System

```
scripts/
├── build_syllabi.py         # Syllabus generation
├── build_schedules.py       # Schedule creation
└── utils/
    ├── jinja_env.py        # Template environment
    └── semester_calendar.py # Calendar utilities
```

## Configuration Files

### Project Configuration

- **[pyproject.toml](../pyproject.toml)** - Python project configuration
- **[.pre-commit-config.yaml](../.pre-commit-config.yaml)** - Code quality hooks
- **[pytest.ini](../pytest.ini)** - Test configuration

### Course Data

- **[academic-calendar.json](../academic-calendar.json)** - Semester calendar
- **[variables/semester.json](../variables/semester.json)** - Semester variables
- **[profiles/instructor.json](../profiles/instructor.json)** - Instructor info

### Task Templates

- **[dashboard/tools/templates/](../dashboard/tools/templates/)** - YAML task templates
  - `fall25_blackboard_ultra.yaml` - Main course setup tasks
  - `fall25_weekly_static.yaml` - Weekly module tasks

## Quick Reference

### Common Commands

```bash
# Dashboard
make dash                    # Start dashboard
make reprioritize           # Run smart prioritization

# Build
make all                    # Build everything
make syllabi                # Generate syllabi
make schedules              # Create schedules

# Development
make test                   # Run tests
make lint                   # Code quality checks
make format                 # Format code
```

### Environment Variables

```env
# Dashboard
DASH_PORT=5055
DASH_HOST=127.0.0.1
FLASK_ENV=development

# Paths
PROJECT_ROOT=/path/to/project
BUILD_DIR=build
SYLLABI_DIR=build/syllabi

# Semester
SEMESTER_NAME="Fall 2025"
SEMESTER_START=2025-08-25
```

### API Endpoints

```http
GET /                       # Dashboard with Now Queue
GET /api/task/<id>         # Get task details
POST /api/task/<id>        # Update task
GET /syllabi/<course>      # View syllabus
GET /view/<filter>         # Filtered views
```

## Testing

### Test Files

- **[tests/test_models.py](../tests/test_models.py)** - Model unit tests
- **[tests/test_dashboard_app.py](../tests/test_dashboard_app.py)** - Dashboard tests
- **[tests/test_phase_detection.py](../tests/test_phase_detection.py)** - Phase logic tests
- **[tests/test_dependency_service.py](../tests/test_dependency_service.py)** - Dependency tests

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=dashboard --cov=scripts

# Specific categories
pytest -m unit
pytest -m integration
```

## Workflow Guides

### Adding a New Course

1. Create directory: `content/courses/NEW_COURSE/`
2. Add JSON data files (use existing courses as templates)
3. Update `dashboard/state/courses.json`
4. Run `make dash-gen` to generate tasks

### Customizing Prioritization

1. Edit `dashboard/tools/priority_contracts.yaml`
2. Adjust coefficients for different factors
3. Modify phase definitions and dates
4. Run `make reprioritize` to apply

### Creating Task Templates

1. Create YAML file in `dashboard/tools/templates/`
2. Define tasks with dependencies and due dates
3. Run `make dash-gen` to generate
4. Run `make reprioritize` to prioritize

## Support Resources

### Documentation

- Flask documentation (local mirror): `docs/flask-reference/`
- Python 3.13 documentation: `docs/reference/docs.python.org/`
- HTMX documentation: `docs/reference/htmx.org/`

### External Links

- [Flask Documentation](https://flask.palletsprojects.com/)
- [UV Package Manager](https://github.com/astral-sh/uv)
- [Bootstrap 5](https://getbootstrap.com/docs/5.1/)
- [HTMX](https://htmx.org/)

## Project Status

### Completed Features ✅

- Smart task prioritization system
- Now Queue with AI-driven task selection
- Dependency-aware task management
- Automated syllabus generation
- Interactive dashboard with HTMX
- Phase-aware prioritization
- Task template system
- Multi-course support

### In Progress 🚧

- LLM-assisted re-ranking (optional)
- Mobile responsive improvements
- Advanced analytics dashboard

### Planned Features 📋

- Multi-user support
- Time tracking
- Progress predictions
- Calendar integration
- Mobile app

## Contact

**Instructor:** Jeffrey Johnson
**Email:** <jjohnson47@alaska.edu>
**Institution:** Kenai Peninsula College
**Semester:** Fall 2025 (August 25 - December 13)

---

*Last Updated: August 22, 2025*
