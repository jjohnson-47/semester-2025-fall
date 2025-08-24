# Fall 2025 Semester Course Management System

> Automated course management, syllabus generation, and task tracking for KPC Fall 2025 semester

## 📚 Overview

This repository provides a complete course management system for Fall 2025 online courses at Kenai Peninsula College. It automates syllabus generation, schedule creation, Blackboard content packaging, and semester preparation tasks using an advanced **Claude Code Task Tool Orchestration System**.

### 🤖 Orchestration System

The Fall 2025 semester preparation was successfully completed using Claude Code's agent orchestration capabilities, coordinating multiple specialized agents:

- **qa-validator agent**: Validated all 44 JSON configuration files (100% pass rate)
- **course-content agent**: Generated all syllabi, schedules, and course materials
- **calendar-sync agent**: Synchronized due dates and resolved conflicts across courses
- **deploy-manager agent**: Prepared production deployment with iframe support

**Status**: ✅ **Fall 2025 Semester Preparation Complete** (All 167 tasks completed successfully)

### Courses Managed

| Course | Title | CRN | Credits |
|--------|-------|-----|---------|
| **MATH 221** | Applied Calculus for Managerial & Social Sciences | 74645 | 3 |
| **MATH 251** | Calculus I | 74647 | 4 |
| **STAT 253** | Applied Statistics for the Sciences | 74688 | 4 |

## 🚀 Quick Start

```bash
# 1. Clone and enter repository
git clone https://github.com/jjohnson-47/semester-2025-fall.git
cd semester-2025-fall

# 2. Initialize environment
make init

# 3. Generate all course materials
make all

# 4. Start task dashboard
make dash
```

## 📁 Repository Structure

```
semester-2025-fall/
├── 📂 content/              # Course-specific content
│   └── courses/            # Per-course JSON data files
├── 📂 dashboard/           # Task management system
│   ├── app.py             # Flask web application
│   ├── templates/         # Dashboard HTML templates
│   └── tools/             # Task generation/validation
├── 📂 scripts/             # Build automation
│   ├── build_syllabi.py   # Syllabus generator
│   ├── build_schedules.py # Schedule generator
│   └── utils/             # Shared utilities
├── 📂 templates/           # Jinja2 templates
│   ├── syllabus.html.j2   # HTML syllabus template
│   └── syllabus.md.j2     # Markdown syllabus template
├── 📂 build/               # Generated outputs (gitignored)
│   ├── syllabi/           # Generated syllabi
│   ├── schedules/         # Course schedules
│   └── blackboard/        # BB import packages
├── 📄 Makefile            # Build orchestration
└── 📄 academic-calendar.json # Fall 2025 calendar data
```

## 🛠️ Build System

### Core Commands

| Command | Description |
|---------|-------------|
| `make help` | Show all available commands |
| `make init` | Initialize environment and install dependencies |
| `make all` | Build everything (syllabi, schedules, packages) |
| `make course COURSE=MATH221` | Build materials for specific course |
| `make clean` | Remove all generated files |

### Content Generation

| Command | Description |
|---------|-------------|
| `make syllabi` | Generate all course syllabi (HTML/MD/PDF) |
| `make schedules` | Create weekly schedule documents |
| `make weekly` | Generate weekly module folders |
| `make packages` | Build Blackboard import packages |

### Dashboard Commands

| Command | Description |
|---------|-------------|
| `make dash` | Start task management dashboard |
| `make dash-gen` | Generate tasks from templates |
| `make dash-validate` | Validate task dependencies |
| `make dash-snapshot` | Create git snapshot of tasks |
| `make dash-open` | Open dashboard in your browser |

## 📊 Task Dashboard with Smart Prioritization

The integrated task dashboard features an AI-driven prioritization system that identifies the most impactful work:

- **URL:** <http://127.0.0.1:5055> (when running)
- **Smart Features:**
  - **Now Queue** - Shows 3-7 most critical tasks across all courses
  - **Chain Head Detection** - Identifies immediately actionable tasks (➜ marker)
  - **Unblock Impact** - Shows how many downstream tasks each action enables
  - **Smart Scoring** - Combines urgency, impact, and strategic value
  - **Phase-Aware** - Adjusts priorities based on semester timeline

### Smart Prioritization System

The system uses multiple signals to identify high-impact work:

1. **Critical Chain Analysis** - Weights tasks by their path to key milestones
2. **Dependency Resolution** - Prioritizes tasks that unblock the most work
3. **Phase Optimization** - Adjusts focus based on pre-launch/launch/in-term phase
4. **Due Date Integration** - Incorporates traditional deadline urgency

Run prioritization:

```bash
make reprioritize
# Or manually:
python dashboard/tools/reprioritize.py \
  --tasks dashboard/state/tasks.json \
  --contracts dashboard/tools/priority_contracts.yaml \
  --semester-first-day 2025-08-25 \
  --write
```

### Task Workflow

```
blocked → todo → in_progress → done
```

### Dashboard Views

- **Now Queue** - AI-prioritized immediate actions
- **Today** - Tasks due today
- **This Week** - Upcoming 7 days
- **Overdue** - Past due tasks
- **Blocked** - Tasks waiting on dependencies
- **All Tasks** - Complete task list with smart scores

## 📝 Course Configuration

### Adding/Updating Course Content

Course data is stored in JSON files under `content/courses/[COURSE_CODE]/`:

```json
// content/courses/MATH221/course_description.json
{
  "text": "Course description here...",
  "credits": 3,
  "course_crn": "74645"
}
```

### Key Configuration Files

| File | Purpose |
|------|---------|
| `academic-calendar.json` | Semester dates, holidays, deadlines |
| `profiles/instructor.json` | Instructor contact information |
| `variables/semester.json` | Semester-wide settings |
| `content/courses/*/` | Course-specific data |

## 📅 Important Dates (Fall 2025)

- **Classes Begin:** August 25, 2025
- **Add/Drop Deadline:** September 5, 2025
- **Withdrawal Deadline:** October 31, 2025
- **Finals Week:** December 8-13, 2025

## 🔧 Development

### Prerequisites

- Python 3.13+
- Git and Make
- Pandoc (optional, for PDF generation)

### Installation

We use `uv` to manage environments and sync dependencies defined in `pyproject.toml`.

```bash
# Install Python and sync deps
make init

# Check toolchain
make check-deps
```

### Testing

```bash
# Validate repository data
make validate

# Run full test suite with coverage
make test

# Lint and format
make lint
make format
```

### API Quick Reference

Base URL (default dev): `http://127.0.0.1:5055`

- `GET /api/tasks?course=MATH221&status=todo` — list/filter tasks
- `POST /api/tasks` — create task (JSON: course, title, status, priority, category)
- `PUT /api/tasks/<id>` — update a task’s status via `{ "status": "in_progress" }`
- `POST /api/tasks/bulk-update` — bulk update tasks `{ filter, update }`
- `GET /api/stats` — high-level stats
- `GET /api/export?format=csv|json|ics` — export tasks

Examples:

```bash
curl 'http://127.0.0.1:5055/api/tasks?course=MATH221'
curl -X POST 'http://127.0.0.1:5055/api/tasks' -H 'Content-Type: application/json' \
  -d '{"course":"MATH221","title":"Create syllabus","status":"todo","priority":"high","category":"setup"}'
curl -X PUT  'http://127.0.0.1:5055/api/tasks/MATH221-001' -H 'Content-Type: application/json' -d '{"status":"completed"}'
curl -X POST 'http://127.0.0.1:5055/api/tasks/bulk-update' -H 'Content-Type: application/json' \
  -d '{"filter":{"course":"MATH221","status":"todo"},"update":{"status":"in_progress"}}'
curl 'http://127.0.0.1:5055/api/export?format=ics'
```

## 📚 Documentation

- [Dashboard Workflow Guide](docs/reference/dashboard.md) - Complete dashboard documentation
- [Course Information](docs/reference/fall-2025-courses.md) - Course details and CRNs
- [API Reference](docs/api/) - Script and module documentation
- [Examples](docs/examples/) - Sample configurations

## 🤝 Contributing

1. Create a feature branch
2. Make changes and test thoroughly
3. Run `make validate`, `make lint`, `make test` before committing
4. Submit pull request with clear description

## 📄 License

This project is for educational use at Kenai Peninsula College / University of Alaska Anchorage.

## 👤 Contact

**Instructor:** Jeffrey Johnson
**Email:** <jjohnson47@alaska.edu>
**Institution:** Kenai Peninsula College

---

*Generated for Fall 2025 Semester (August 25 - December 13, 2025)*
