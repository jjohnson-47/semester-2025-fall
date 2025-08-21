# Fall 2025 Semester Course Management System

Automated syllabus generation, schedule building, and Blackboard content packaging for KPC Fall 2025 courses.

## Courses

- **MATH 221** - Mathematical Explorations (CRN: 74645)
- **MATH 251** - Calculus I (CRN: 74647)  
- **STAT 253** - Applied Statistics for the Sciences (CRN: 74688)

## Quick Start

```bash
# Initial setup
make init

# Build everything
make all

# Build specific course
make course COURSE=MATH221
```

## Project Structure

```
semester-2025-fall/
├── scripts/              # Build automation scripts
├── templates/            # Jinja2 templates for syllabi and Blackboard content
├── variables/            # Semester-level configuration
├── content/              # Course-specific content
│   └── courses/          # Per-course data files
├── build/                # Generated outputs (gitignored)
└── Makefile              # Build orchestration
```

## Key Features

- **Data-Driven**: All content generated from JSON configuration files
- **Multi-Format**: Generate HTML, Markdown, and PDF syllabi
- **Blackboard Ready**: Creates importable content packages
- **Schedule Automation**: Auto-generates weekly schedules from academic calendar
- **Validation**: JSON schema validation ensures data consistency

## Build Targets

| Target | Description |
|--------|-------------|
| `make init` | Setup environment and validate configuration |
| `make validate` | Validate all JSON files against schemas |
| `make syllabi` | Generate all course syllabi |
| `make schedules` | Generate course schedules |
| `make packages` | Build Blackboard import packages |
| `make all` | Complete build pipeline |

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
SEMESTER_CODE=202503
TIMEZONE=America/Anchorage
INSTRUCTOR_NAME="Jeffrey Johnson"
```

### Course Data

Course-specific data is stored in `content/courses/[COURSE_CODE]/`:
- `introduction.json` - Course introduction
- `course_description.json` - Official catalog description  
- `evaluation_tools.json` - Assessment categories and weights
- `grading_policy.json` - Grade scale and policies
- Additional content modules as needed

## Development

### Prerequisites

- Python 3.9+
- Make
- Git

### Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run validation
make validate
```

### Testing

```bash
# Dry run (no files written)
make validate

# Test single course build
make course COURSE=MATH221
```

## Output

Generated files are placed in `build/`:
- `syllabi/` - Course syllabi (MD, HTML, PDF)
- `schedules/` - Weekly schedules
- `blackboard/` - Blackboard import packages

## Documentation

- [Setup Guide](docs/setup.md)
- [Data Schema Reference](docs/schemas.md)
- [Template Guide](docs/templates.md)

## Support

Jeffrey Johnson - jjohnson47@alaska.edu

---

*Generated for Fall 2025 Semester (August 25 - December 13, 2025)*