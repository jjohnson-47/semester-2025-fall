# Project: Fall 2025 Course Management System
## Kenai Peninsula College Academic Content Platform

## 🎯 Architecture Overview
- **Core**: Python 3.13 with UV package manager (no venv/pip)
- **Build System**: GNU Make with V2 projection-based architecture
- **Template Engine**: Jinja2 with custom projection adapters
- **Dashboard**: Flask web application on port 5055
- **Database**: JSON-based content storage in `content/courses/`
- **Deployment**: GitHub Actions → Cloudflare Pages (https://courses.jeffsthings.com)
- **Testing**: Pytest with property-based tests via Hypothesis

## 📂 Project Structure
```
.
├── content/courses/         # Source of truth for course data
│   ├── MATH221/            # Intermediate Algebra
│   ├── MATH251/            # Calculus I
│   └── STAT253/            # Statistics I
├── scripts/                # Build and validation scripts
│   ├── services/           # V2 CourseService, ValidationGateway
│   ├── rules/              # Business rule engine (no weekend dues)
│   ├── utils/              # StyleSystem, CSS handlers
│   └── builders/           # Projection adapters for rendering
├── dashboard/              # Flask management dashboard
│   ├── agents/             # Specialized automation agents
│   ├── api/                # RESTful deployment endpoints
│   ├── db/                 # SQLite tracking database
│   └── templates/          # Dashboard UI templates
├── templates/              # Jinja2 templates for content
├── tests/                  # Comprehensive test suite
│   ├── contracts/          # Contract-based testing
│   ├── integration/        # Full pipeline tests
│   ├── property/           # Property-based tests with Hypothesis
│   └── semantic/           # HTML diff validation
├── build/                  # Generated output (gitignored)
│   ├── syllabi/            # Generated syllabus HTML
│   ├── schedules/          # Generated schedule HTML
│   └── blackboard/         # DOCX exports for Blackboard
└── site/                   # Static site for deployment
```

## 🚀 Development Commands

### Essential Make Targets (ALWAYS use BUILD_MODE=v2)
```bash
# Core build commands
BUILD_MODE=v2 make all          # Build everything
BUILD_MODE=v2 make validate     # Validate JSON schemas
BUILD_MODE=v2 make test         # Run full test suite
BUILD_MODE=v2 make clean        # Clean build artifacts

# Course-specific builds
BUILD_MODE=v2 make course COURSE=MATH221  # Build single course
BUILD_MODE=v2 make syllabi               # Build all syllabi
BUILD_MODE=v2 make schedules              # Build all schedules

# Dashboard operations
DASH_PORT=5055 BUILD_MODE=v2 make dash         # Start dashboard
BUILD_MODE=v2 make dash-gen                    # Generate tasks
BUILD_MODE=v2 make dash-prioritize             # Prioritize tasks

# Deployment
BUILD_MODE=v2 make build-site   # Prepare for deployment
BUILD_MODE=v2 make deploy        # Deploy to production
```

### Python Script Commands
```bash
# Direct script execution (always use uv run)
uv run python scripts/build_syllabi.py
uv run python scripts/build_schedules.py
uv run python scripts/validate_v110.py
uv run python scripts/site_build.py

# Dashboard server
uv run python -m dashboard.app

# Testing
uv run pytest tests/ -v
uv run pytest tests/contracts/ -v
uv run pytest tests/property/ -v --hypothesis-show-statistics
```

### Dashboard Web Interface
```bash
# Access dashboard at http://localhost:5055
# Features:
# - One-click deployment to Cloudflare
# - DOCX export for Blackboard
# - Task management and tracking
# - Build statistics monitoring
```

## 🎓 Course Configuration

### MATH 221 - Intermediate Algebra
- **Schedule**: MWF 8:00-8:50 AM
- **Theme**: Blue (#0066cc)
- **Content**: `content/courses/MATH221/`

### MATH 251 - Calculus I  
- **Schedule**: MWF 9:00-9:50 AM
- **Theme**: Green (#006600)
- **Content**: `content/courses/MATH251/`
- **Special**: Interactive limit calculator tool

### STAT 253 - Statistics I
- **Schedule**: TTh 10:00-11:15 AM
- **Theme**: Orange (#cc6600)
- **Content**: `content/courses/STAT253/`

## 📅 Academic Calendar
- **Semester**: August 25 - December 13, 2025
- **Add/Drop Deadline**: September 5, 2025
- **Withdrawal Deadline**: October 31, 2025
- **Finals Week**: December 8-12, 2025
- **No Classes**: Labor Day (Sep 1), Thanksgiving (Nov 27-28)

## 🔧 Current Focus & Tasks
- Maintaining V2 projection-based architecture
- Ensuring no weekend due dates via rules engine
- Supporting iframe embedding for Blackboard
- Dashboard API for automated deployments
- Property-based testing for data validation

## 🏗️ System Conventions

### Code Style
- Python: Black formatter, 100 char lines, Ruff linting
- Type hints required for all functions
- Comprehensive docstrings (Google style)
- Property-based tests where applicable
- 80%+ test coverage target

### Architecture Patterns
- **Projection System**: Transform data once, render many times
- **Rules Engine**: Centralized business logic enforcement
- **Style System**: Course-specific theming with embedded CSS
- **Validation Gateway**: Schema v1.1.0 compliance layer
- **Task Orchestration**: Agent-based complex workflows

### Git Workflow
- Branch naming: `feat/`, `fix/`, `docs/`, `refactor/`
- Conventional commits format
- Never commit to main directly
- PR reviews required for production changes
- GitHub Actions for CI/CD

## 🔒 Security Requirements
- No hardcoded credentials (use .env files)
- CSP headers configured for iframe embedding
- Input validation on all user data
- Sanitized HTML output
- Environment-based configuration
- Gopass integration for secrets (agent-accessible paths only)

## ⚡ Performance Targets
- Build time: < 10 seconds for full rebuild
- Dashboard response: < 200ms for API calls
- Page load: < 1 second for static content
- Test suite: < 30 seconds for full run
- Memory usage: < 500MB during builds

## 🤖 AI Agent Notes

### Available MCP Servers
- **filesystem**: Full project file access
- **github**: Repository and PR management
- **memory-bank**: Persistent context tracking
- **puppeteer**: Browser automation testing
- **fetch**: Web content retrieval
- **brave-search**: Documentation lookup

### Task Automation Agents
When encountering complex multi-step tasks, use the Task tool:
- `orchestrator`: Master coordinator for workflows
- `qa-validator`: JSON validation and compliance
- `course-content`: Syllabus/schedule generation
- `deploy-manager`: Site building and deployment
- `calendar-sync`: Date management and consistency

### Critical Rules
1. **ALWAYS use BUILD_MODE=v2** - Legacy mode is deprecated
2. **Never create weekend due dates** - Rules engine enforces this
3. **Validate before building** - Run validation checks first
4. **Test before deploying** - Full test suite must pass
5. **Use UV for Python** - Never use pip or venv directly
6. **Embed CSS in HTML** - For standalone file viewing

### Common Gotchas
- Module imports: Always use `uv run python` not bare `python`
- Dashboard state: Check `dashboard/state/tasks.json` for issues
- Date adjustments: Rules engine auto-adjusts weekend dates
- Build artifacts: Never commit `build/` directory
- Stable IDs: Maintain `_meta.id` fields in JSON

## 🔄 Integration Points

### With Global Codex Config
- Inherits from `~/.codex/AGENTS.md` for system preferences
- Uses GPT-5 models as configured globally
- Respects agent profile for automation tasks
- Follows global security practices

### With GitHub Actions
- CI/CD pipeline in `.github/workflows/`
- Automated deployment on main branch push
- Test validation before deployment
- Cloudflare Pages integration

### With Cloudflare Pages
- Production URL: https://courses.jeffsthings.com
- Automatic deployments from GitHub
- Custom domain configuration
- Edge caching for performance

## 📚 Key Documentation
- `README.md` - Project overview and setup
- `CLAUDE.md` - Claude Code specific instructions
- `docs/IMPLEMENTATION_STATUS.md` - V2 progress tracking
- `docs/adr/` - Architecture decision records
- `dashboard/API_DOCUMENTATION.md` - Dashboard API reference

## 🆘 Quick Troubleshooting

### Import Errors
```bash
uv sync --extra dashboard --extra testing
```

### Dashboard Won't Start
```bash
DASH_PORT=5055 BUILD_MODE=v2 uv run python -m dashboard.app
```

### Tests Failing
```bash
BUILD_MODE=v2 make validate  # Check JSON first
BUILD_MODE=v2 make test      # Run full suite
```

### Build Errors
```bash
BUILD_MODE=v2 make clean     # Clear artifacts
BUILD_MODE=v2 make all       # Rebuild everything
```

---

**Project Status**: Active Development
**Architecture**: V2 Projection-based with Rules Engine
**Last Updated**: September 2025
**Python**: 3.13+ | UV: 0.8.14+ | Make: 4.4.1+