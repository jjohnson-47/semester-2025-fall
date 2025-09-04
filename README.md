# Fall 2025 Semester Course Management System (V2 Architecture)

> Automated course management with projection-based rendering, systematic rule enforcement, and one-click deployment

## 📚 Overview

This repository provides a complete course management system for Fall 2025 online courses at Kenai Peninsula College using the **V2 Architecture**. It features projection-based rendering, embedded CSS styling, systematic rule enforcement (no weekend due dates), and integrated deployment to Cloudflare Pages.

**⚡ IMPORTANT: Always use `BUILD_MODE=v2` for all operations. Legacy mode is deprecated.**

### 🤖 Orchestration System

The Fall 2025 semester preparation was successfully completed using Claude Code's agent orchestration capabilities, coordinating multiple specialized agents:

- **qa-validator agent**: Validated all 44 JSON configuration files (100% pass rate)
- **course-content agent**: Generated all syllabi, schedules, and course materials
- **calendar-sync agent**: Synchronized due dates and resolved conflicts across courses
- **deploy-manager agent**: Prepared production deployment with iframe support

**Status**: ✅ **Fall 2025 Semester Preparation Complete** (All 167 tasks completed successfully)

### 🌟 Content Delivery Architecture

**Content Factory** (this repository): 
- JSON configuration files
- Jinja2 templates
- Build automation scripts
- Task management dashboard

**Content Delivery** ([jeffsthings-courses](https://github.com/jjohnson-47/jeffsthings-courses)):
- Static site generation from factory output
- Production deployment at https://courses.jeffsthings.com/
- Blackboard Ultra iframe integration

### Courses Managed

| Course | Title | CRN | Credits |
|--------|-------|-----|---------|
| **MATH 221** | Applied Calculus for Managerial & Social Sciences | 74645 | 3 |
| **MATH 251** | Calculus I | 74647 | 4 |
| **STAT 253** | Applied Statistics for the Sciences | 74688 | 4 |

## 🚀 Quick Start (V2 Mode)

```bash
# 1. Clone and enter repository
git clone https://github.com/jjohnson-47/semester-2025-fall.git
cd semester-2025-fall

# 2. Initialize environment
make init

# 3. Generate all course materials (V2 Architecture)
BUILD_MODE=v2 make all

# 4. Start task dashboard with V2 mode
BUILD_MODE=v2 make dash

# 5. Access dashboard at http://localhost:5055
# Click "Deploy" → "Deploy to Production" for one-click deployment
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

## 🛠️ Build System (V2 Architecture)

### Core Commands - Always Use BUILD_MODE=v2

| Command | Description |
|---------|-------------|
| `make help` | Show all available commands |
| `make init` | Initialize environment and install dependencies |
| `BUILD_MODE=v2 make all` | Build everything with V2 architecture |
| `BUILD_MODE=v2 make course COURSE=MATH221` | Build materials for specific course |
| `make clean` | Remove all generated files |

### Content Generation (V2 Mode Required)

| Command | Description |
|---------|-------------|
| `BUILD_MODE=v2 make syllabi` | Generate syllabi with embedded CSS |
| `BUILD_MODE=v2 make schedules` | Create schedules with course themes |
| `BUILD_MODE=v2 make pipeline` | Run complete V2 pipeline |
| `BUILD_MODE=v2 make test` | Test V2 rule enforcement |
| `make weekly` | Generate weekly module folders |
| `make packages` | Build Blackboard import packages |

## 🔬 V2 Architecture Features

The V2 architecture is the **primary and recommended mode** for all operations. Legacy mode is deprecated and will be removed.

### Core V2 Features

- **Projection-Based Rendering**: Transform course data through purpose-specific projections
- **Embedded CSS Styling**: Course-specific themes (MATH221: Blue, MATH251: Green, STAT253: Orange)
- **Rules Engine**: Systematic enforcement of "no weekend due dates" policy
- **Style System**: Context-aware CSS management for standalone and embedded viewing
- **Schema v1.1.0**: Enhanced JSON with stable IDs and metadata tracking
- **One-Click Deployment**: Dashboard button deploys directly to Cloudflare Pages

### V2 Build Mode

Enable v2 features with the `BUILD_MODE=v2` environment variable:

```bash
# Enable v2 projection system
BUILD_MODE=v2 make schedules

# Preview v2 schedule projection  
BUILD_MODE=v2 python -c "
from scripts.services.course_service import CourseService
import json
s = CourseService('MATH221')
ctx = s.get_template_context('schedule')
print(json.dumps(ctx.get('schedule_projection', {}), indent=2))
"

# Generate v2 site preview
BUILD_MODE=v2 make all
```

### Schema Validation and Migration

| Command | Description |
|---------|-------------|
| `make validate-v110` | Validate all schedules against v1.1.0 schema |
| `make ids-dry-run` | Generate stable IDs into build/normalized/ (dry-run) |
| `make pipeline` | Run enhanced build pipeline with reports |

#### Enhanced Pipeline (flags)

```bash
# Run all stages with verbose logs
$(PYTHON) scripts/build_pipeline.py --courses MATH221 MATH251 STAT253 -v

# Simulate without writing files
$(PYTHON) scripts/build_pipeline.py --courses MATH221 --dry-run

# Run a single stage (e.g., projection)
$(PYTHON) scripts/build_pipeline.py --courses MATH221 --stage project
```

### V2 Quality Assurance

```bash
# Validate no weekend due dates across all courses
BUILD_MODE=v2 python -c "
from scripts.services.course_service import CourseService
for course in ['MATH221', 'MATH251', 'STAT253']:
    s = CourseService(course)
    ctx = s.get_template_context('schedule')
    if 'schedule_projection' in ctx:
        proj = ctx['schedule_projection']
        weekend_count = sum(
            1 for w in proj.get('weeks', [])
            for item in w.get('assignments', []) + w.get('assessments', [])
            if '(due Sat' in str(item) or '(due Sun' in str(item)
        )
        print(f'{course}: {weekend_count} weekend due dates (should be 0)')
"

# Run enhanced test suite
pytest tests/golden/ tests/contracts/ tests/property/ -v

# Generate HTML comparison report
python tests/semantic/test_html_diff_v2.py
```

### Deprecations (Fall 2025)

- Some compatibility shims exist to complete merges of pre‑refactor branches:
  - `scripts/build_pipeline_impl.py` → use `scripts/build_pipeline.py`
  - `scripts/rules/dates_full.py` → use `scripts/rules/dates.py`
  - `scripts/schema/migrator.py` → use `scripts.migrations.add_stable_ids`
  - `scripts/utils/schema/versions/v1_1_0.py` (module file) → import from the package path
- These emit `DeprecationWarning` and will be removed after Fall 2025. See `docs/DEPRECATIONS.md`.

### Migration Path

**Phase 1: Validation & Testing** (Current)
```bash
# Test v2 mode locally
BUILD_MODE=v2 make all

# Validate output
make validate-v110

# Run comprehensive tests  
make test
```

**Phase 2: Gradual Adoption**
```bash
# Use v2 for specific courses
BUILD_MODE=v2 make course COURSE=MATH221

# Compare outputs
diff -r build/schedules/ build/v2/

# Deploy to staging
BUILD_MODE=v2 make deploy-staging
```

**Phase 3: Full Cutover**
```bash
# Enable v2 globally
export BUILD_MODE=v2

# Update configuration
echo 'BUILD_MODE=v2' >> .env

# Full production build
make clean all deploy
```

### V2 Architecture Benefits

- **Data Quality**: Schema validation catches errors early
- **Consistency**: Centralized rules ensure uniform behavior
- **Traceability**: Full provenance tracking for all transformations
- **Maintainability**: Projection-based architecture simplifies templates
- **Reliability**: No weekend due dates systematically enforced

## 🚀 Deployment to Production

### Recommended: Dashboard One-Click Deploy

1. Start dashboard with V2 mode:
```bash
BUILD_MODE=v2 make dash
```

2. Navigate to http://localhost:5055

3. Click **Deploy** button in top navigation

4. Select **Deploy to Production**

The system automatically:
- Builds with V2 architecture
- Syncs to deployment repository  
- Deploys to Cloudflare Pages
- Verifies iframe functionality

**Production URLs:**
- Primary: https://courses.jeffsthings.com/
- Fallback: https://production.jeffsthings-courses.pages.dev/

### Manual Deployment

```bash
# Build static site with V2
BUILD_MODE=v2 make build-site

# Commit and push (triggers GitHub Actions)
git add -A
git commit -m "Deploy updates"
git push origin main
```

### Dashboard Commands

| Command | Description |
|---------|-------------|
| `BUILD_MODE=v2 make dash` | Start dashboard with V2 mode |
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

## 🎮 Interactive Tools

The repository includes interactive HTML tools for mathematics education:

### MATH 251 - A δ for your ε
**Location:** `site/interactive/math251/epsilon-delta.html`
**Production URL:** https://courses.jeffsthings.com/interactive/math251/epsilon-delta.html

Interactive visualization tool for teaching the rigorous epsilon–delta definition of limits:
- **Learn Mode:** Step-by-step guided instruction
- **Practice Mode:** Self-directed problem solving  
- **Challenge Mode:** Timed progression through 5 function levels
- **Features:** Real-time graph visualization, KaTeX rendering (local vendor), progress tracking

**Iframe Embedding for Blackboard Ultra:**
```html
<iframe 
    src="https://courses.jeffsthings.com/interactive/math251/epsilon-delta.html" 
    width="100%" 
    height="800" 
    frameborder="0" 
    allowfullscreen>
</iframe>
```

### Local Testing
```bash
python -m http.server 8002 -d site/interactive
# Visit: http://localhost:8002/math251/epsilon-delta.html
```

## 📚 Documentation

- [Interactive Tools Development Guide](docs/INTERACTIVE_TOOLS_GUIDE.md) - Complete guide with lessons learned
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
