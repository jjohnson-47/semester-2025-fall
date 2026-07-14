# Course Management System - Fall 2025 Semester
## Claude Code CLI Configuration (July 2026)

This document provides comprehensive context and instructions for Claude Code CLI v3.0+ working on the KPC Fall 2025 semester course management system.

> **Current posture (2026-07-14): Retained public archive.** The Fall 2025
> teaching period is complete. Automatic Pages deployment, scheduled
> maintenance, and dashboard deployment controls are retired. Local
> `BUILD_MODE=v2` validation and archive builds remain supported. Publication
> reactivation requires a new explicit owner decision and
> `docs/adr/0005-retained-public-archive.md`.

## 🎯 Project Overview

- **Purpose**: Preserve reproducible course material generation for Kenai Peninsula College Fall 2025
- **Architecture**: V2 Projection-based system with rule enforcement
- **Courses**: MATH 221 (Intermediate Algebra), MATH 251 (Calculus I), STAT 253 (Statistics I)
- **Publication**: Retained public archive (<https://courses.jeffsthings.com>); automation retired

## 🏗️ Technical Stack

- **Language**: Python 3.13+ with UV package manager
- **Build**: GNU Make with BUILD_MODE=v2 (legacy deprecated)
- **Templates**: Jinja2 with projection system
- **Dashboard**: Flask on port 5055
- **Testing**: Pytest with property-based tests via Hypothesis
- **Publication**: Existing Cloudflare Pages output retained; repository automation retired

## 📁 Project Structure

```
semester-2025-fall/
├── content/courses/     # Course JSON data (source of truth)
│   ├── MATH221/        # schedule.json, syllabus.json, bb_content.json
│   ├── MATH251/        
│   └── STAT253/        
├── scripts/            
│   ├── services/       # V2 CourseService, ValidationGateway
│   ├── rules/          # Date rules, business logic enforcement
│   ├── utils/          # StyleSystem, CSS handlers
│   └── builders/       # Projection adapters for rendering
├── dashboard/          # Flask task management (http://localhost:5055)
│   ├── agents/         # Specialized automation agents
│   ├── api/            # RESTful endpoints
│   └── templates/      # UI templates
├── templates/          # Jinja2 templates for content generation
├── tests/              
│   ├── contracts/      # Contract-based testing
│   ├── integration/    # Full pipeline tests
│   ├── property/       # Property-based tests
│   └── semantic/       # HTML diff validation
├── build/              # Generated output (gitignored)
│   ├── syllabi/        
│   ├── schedules/      
│   └── blackboard/     
└── site/               # Static archive output
```

## ⚡ Critical Commands

### Daily Development Workflow
```bash
# Always use V2 mode - legacy is deprecated
BUILD_MODE=v2 make all          # Build everything
BUILD_MODE=v2 make validate     # Validate JSON schemas
BUILD_MODE=v2 make test         # Run test suite

# Dashboard operations
DASH_PORT=5055 BUILD_MODE=v2 make dash    # Start dashboard
BUILD_MODE=v2 make dash-gen              # Generate tasks

# Course-specific builds
BUILD_MODE=v2 make course COURSE=MATH221  # Single course

# Retained archive verification (local only)
BUILD_MODE=v2 make build-site
test -f site/manifest.json
test -f site/_headers
```

## 🎨 V2 Architecture Components

### Core Systems

1. **Projection System** (`scripts/services/projection_adapter.py`)
   - Transforms course data into template-ready projections
   - Enforces business rules uniformly
   - Handles date adjustments and validation

2. **Rules Engine** (`scripts/rules/`)
   - No weekend due dates (automatic adjustment)
   - Schema v1.1.0 compliance
   - Date consistency enforcement

3. **Style System** (`scripts/utils/style_system.py`)
   - Course-specific themes:
     - MATH221: Blue (#0066cc)
     - MATH251: Green (#006600)
     - STAT253: Orange (#cc6600)
   - Embedded CSS for standalone viewing

4. **Dashboard** (http://localhost:5055)
   - Task management and tracking
   - Local archive inspection; publication controls are retired
   - DOCX export capabilities
   - Build statistics and monitoring

## 🔄 MCP Server Integration

This project supports MCP (Model Context Protocol) servers for enhanced capabilities:

### Available MCP Servers
- **filesystem**: File operations within project bounds
- **github**: Repository management and PR creation
- **memory-bank**: Persistent context and decision tracking
- **puppeteer**: Browser automation for testing
- **fetch**: Web content retrieval
- **brave-search**: Web search capabilities
- **sequential-thinking**: Complex reasoning chains

### MCP Configuration
Located in user settings, not project-specific. Servers auto-connect when Claude Code starts.

## 🤖 Agentic Capabilities

### Specialized Subagents
When encountering complex multi-step tasks, use the Task tool to spawn specialized agents:

- **orchestrator**: Master coordinator for complex workflows
- **qa-validator**: JSON validation, schema compliance, date consistency
- **course-content**: Syllabus/schedule generation, material creation
- **calendar-sync**: Date propagation and conflict resolution

Historical records may refer to a `deploy-manager`, but it is not an authorized
current publication path.

### Workflow Patterns
```bash
# Complex archive verification
Task(subagent_type="orchestrator",
     prompt="Verify the retained Fall 2025 archive without publishing")

# Validation and fixes
Task(subagent_type="qa-validator",
     prompt="Validate all course JSON and fix date issues")
```

## ✅ Development Best Practices

### Pre-commit Checklist
1. **Always validate**: `BUILD_MODE=v2 make validate`
2. **Run tests**: `BUILD_MODE=v2 make test`
3. **Check no weekend dues**: Automatically enforced
4. **Verify stable IDs**: `_meta.id` fields present

### Code Standards
- Python 3.13+ with type hints
- Ruff for linting (configured in pyproject.toml)
- Black for formatting (100 char lines)
- Comprehensive docstrings
- Property-based testing where applicable

### Security Requirements
- Never commit credentials or API keys
- CSP headers configured for iframe embedding
- Environment variables for sensitive config
- Gopass integration for secret management

## 📅 Academic Calendar

- **Semester**: August 25 - December 13, 2025
- **Add/Drop**: September 5, 2025
- **Withdrawal**: October 31, 2025
- **Finals Week**: December 8-12, 2025

### Course Schedule
- MATH 221: MWF 8:00-8:50 AM
- MATH 251: MWF 9:00-9:50 AM  
- STAT 253: TTh 10:00-11:15 AM

## 🐛 Common Issues & Solutions

### Build Failures
```bash
# Always use V2 mode
BUILD_MODE=v2 make all

# Check validation first
make validate

# Review logs
ls -la scripts/logs/
```

### Dashboard Issues
```bash
# Restart with correct mode
DASH_PORT=5055 BUILD_MODE=v2 uv run python -m dashboard.app

# Check state files
cat dashboard/state/tasks.json
```

### Module Import Errors
```bash
# Ensure UV sync
uv sync --extra dashboard

# Use UV to run scripts
uv run python scripts/build_syllabi.py
```

## 🗄️ Archive Verification

The current supported workflow rebuilds and validates archive output locally:

```bash
BUILD_MODE=v2 make validate
BUILD_MODE=v2 make test
BUILD_MODE=v2 make build-site ENV=preview
test -f site/manifest.json
test -f site/_headers
```

These commands do not publish. Pushing to `main` does not deploy the site. Do
not create, rotate, retrieve, or install Cloudflare credentials merely to
publish repository changes. Reactivation requires a new explicit owner decision
and the requirements in `docs/adr/0005-retained-public-archive.md`.

## 📝 Task Management with TodoWrite

For complex multi-step operations, always use TodoWrite to track progress:

```python
# Example workflow tracking
todos = [
    {"content": "Validate all course JSON", "status": "pending"},
    {"content": "Generate syllabi with V2", "status": "pending"},
    {"content": "Run integration tests", "status": "pending"},
    {"content": "Build preview archive locally", "status": "pending"},
    {"content": "Verify archive output", "status": "pending"}
]
```

## 🔒 Permissions & Boundaries

### Allowed Operations
- All file operations within project directory
- UV and Make commands
- Dashboard state management
- Git operations (except direct .git/ manipulation)
- Test execution and validation

### Restricted Operations
- Direct pip/venv usage (use UV instead)
- System package installation
- Any publication or publication reactivation without a new explicit owner decision
- Manual uv.lock editing
- Legacy BUILD_MODE usage

## 💡 Performance Optimizations

- UV package caching for fast reinstalls
- Make dependency tracking for incremental builds
- Parallel test execution with pytest-xdist
- Dashboard file locking for concurrent access
- Minimal JavaScript for fast page loads

## 📚 Key Documentation

Essential project docs for deep dives:

- `docs/IMPLEMENTATION_STATUS.md` - V2 implementation progress
- `docs/adr/` - Architecture Decision Records
- `docs/adr/0005-retained-public-archive.md` - Current publication decision and reactivation gate
- `dashboard/API_DOCUMENTATION.md` - Dashboard API reference
- `docs/V2_DEPLOYMENT_GUIDE.md` - Historical deployment procedures only
- `README.md` - Project overview and setup

## 🎯 Quick Decision Guide

| Task | Command/Approach |
|------|-----------------|
| Build all materials | `BUILD_MODE=v2 make all` |
| Start dashboard | `BUILD_MODE=v2 make dash` |
| Validate changes | `make validate` |
| Run tests | `BUILD_MODE=v2 make test` |
| Publish or reactivate | Not authorized; requires a new owner decision and ADR 0005 |
| Debug issues | Check `scripts/logs/` and `dashboard/logs/` |
| Add new course | Outside retained-archive scope; obtain owner direction first |
| Complex task | Use Task tool with orchestrator agent |

## ⚠️ Critical Rules

1. **NEVER use legacy mode** - Always BUILD_MODE=v2
2. **No weekend due dates** - Automatically enforced
3. **Validate before building** - Run `make validate`
4. **Do not publish** - Reactivation requires a new explicit owner decision and ADR 0005
5. **Use stable IDs** - Maintain `_meta.id` fields
6. **Document decisions** - Update ADRs for architecture changes

## 🔄 Migration Notes

When encountering legacy code:
1. Check for V2 equivalent in `scripts/services/`
2. Use projection-based rendering
3. Embed CSS for standalone files
4. Update to use BUILD_MODE=v2

## 🚫 Do NOT

- Use BUILD_MODE=v1 or legacy mode
- Edit generated HTML directly
- Publish or restore publication without a new explicit owner decision
- Bypass the rules engine
- Create weekend due dates
- Use hardcoded absolute paths
- Commit build/ directory contents
- Use pip/venv directly (use UV)

---

*Last updated: July 14, 2026 - retained public archive configuration*
*Architecture: V2 Projection-based with MCP integration*
*Python: 3.13+ | UV: 0.8.14 | Make: 4.4.1*
