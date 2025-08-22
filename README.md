# Fall 2025 Semester Course Management System

> Automated course management, syllabus generation, and task tracking for KPC Fall 2025 semester

## 📚 Overview

This repository provides a complete course management system for Fall 2025 online courses at Kenai Peninsula College. It automates syllabus generation, schedule creation, Blackboard content packaging, and semester preparation tasks.

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

## 📊 Task Dashboard

The integrated task dashboard helps track semester preparation:

- **URL:** <http://127.0.0.1:5055> (when running)
- **Features:**
  - Visual task tracking with 5 status levels
  - Automatic dependency resolution
  - Due date monitoring and alerts
  - Checklist support for complex tasks
  - Git-backed task history

### Task Workflow

```
blocked → todo → doing → review → done
```

### Dashboard Views

- **Today** - Tasks due today
- **This Week** - Upcoming 7 days
- **Overdue** - Past due tasks
- **Blocked** - Tasks waiting on dependencies
- **All Tasks** - Complete task list

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

- Python 3.9+
- Git
- Make
- Pandoc (optional, for PDF generation)

### Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r dashboard/requirements.txt
```

### Testing

```bash
# Validate all JSON files
make validate

# Run dashboard validation
make dash-validate

# Check dependencies
make check-deps
```

## 📚 Documentation

- [Dashboard Workflow Guide](docs/reference/dashboard.md) - Complete dashboard documentation
- [Course Information](docs/reference/fall-2025-courses.md) - Course details and CRNs
- [API Reference](docs/api/) - Script and module documentation
- [Examples](docs/examples/) - Sample configurations

## 🤝 Contributing

1. Create a feature branch
2. Make changes and test thoroughly
3. Run `make validate` before committing
4. Submit pull request with clear description

## 📄 License

This project is for educational use at Kenai Peninsula College / University of Alaska Anchorage.

## 👤 Contact

**Instructor:** Jeffrey Johnson
**Email:** <jjohnson47@alaska.edu>
**Institution:** Kenai Peninsula College

---

*Generated for Fall 2025 Semester (August 25 - December 13, 2025)*
