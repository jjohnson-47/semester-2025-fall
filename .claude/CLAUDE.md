# KPC Fall 2025 Semester Management System

## Project Context for Claude Code - August 2025

This is an academic course management system for Kenai Peninsula College's Fall 2025 semester.
The system automates syllabus generation, schedule creation, and task management for mathematics courses.

## Project Overview

### Primary Purpose

Automate and streamline course preparation and management for:

- MATH 221: Intermediate Algebra
- MATH 251: Calculus I
- STAT 253: Statistics I

### Key Systems

1. **Build System**: Make-based orchestration with UV package management
2. **Content Generation**: Jinja2 templating for syllabi, schedules, and course materials
3. **Task Dashboard**: Flask-based web interface for semester task tracking
4. **Validation**: JSON schema validation for all configuration files

## Technical Stack

### Core Technologies

- **Language**: Python 3.11+ with UV package manager
- **Build**: GNU Make with color-coded output
- **Templates**: Jinja2 with custom filters
- **Web**: Flask for dashboard (port 5055)
- **Data**: JSON for configuration, YAML for task templates
- **VCS**: Git with GitHub (jjohnson-47 account)

### Project Structure

```
semester-2025-fall/
├── content/courses/     # Course JSON data (schedule, syllabus, bb_content)
├── templates/           # Jinja2 templates for content generation
├── scripts/            # Python build and utility scripts
├── dashboard/          # Flask task management application
├── build/             # Generated output (syllabi, schedules, packages)
└── .claude/           # Claude Code configuration
```

## Key Commands

### Essential Make Targets

- `make init` - Initialize UV environment
- `make all` - Complete build for all courses
- `make syllabi` - Generate all syllabi
- `make dash` - Launch task dashboard
- `make dash-gen` - Generate tasks from templates
- `make course COURSE=MATH221` - Build specific course

### UV Commands

- `uv sync` - Install dependencies
- `uv sync --extra dashboard` - Install with dashboard deps
- `uv run python <script>` - Run scripts in UV environment
- `uv lock --upgrade` - Update all dependencies

## Development Workflow

### When Building Syllabi

1. Edit course JSON in `content/courses/<COURSE>/`
2. Run `make validate` to check JSON
3. Run `make syllabi` to generate
4. Check output in `build/syllabi/`

### When Working on Dashboard

1. Run `make dash-gen` to create tasks
2. Run `make dash` to start server
3. Access at <http://127.0.0.1:5055>
4. Tasks auto-save to `dashboard/state/tasks.json`

### When Adding Dependencies

1. Edit `pyproject.toml`
2. Run `uv lock` to update lockfile
3. Run `uv sync` to install

## Critical Files

### Configuration

- `pyproject.toml` - Python dependencies and project metadata
- `uv.lock` - Locked dependency versions
- `Makefile` - Build orchestration
- `.env` - Environment variables (if exists)

### Course Data

- `content/courses/*/schedule.json` - Weekly topics and assignments
- `content/courses/*/syllabus.json` - Course policies and info
- `content/courses/*/bb_content.json` - Blackboard integration data

### Templates

- `templates/syllabus.html.j2` - Main syllabus template
- `templates/schedule.html.j2` - Schedule template
- `dashboard/templates/` - Dashboard UI templates

## Important Behaviors

### Validation

- All JSON files are validated against schemas before builds
- Validation errors block the build process
- Run `make validate` to check all files

### Task Management

- Tasks have 5 states: blocked → todo → doing → review → done
- Tasks auto-snapshot to Git on major changes
- Dashboard uses file locking for concurrent access

### Calendar System

- Semester dates from `variables/*.json`
- Automatic week numbering and date calculation
- Holiday and break awareness

## Common Issues & Solutions

### Issue: Module import errors

**Solution**: Ensure `uv sync` has run and use `uv run python` for scripts

### Issue: Calendar import conflict

**Solution**: Module renamed to `semester_calendar.py` to avoid stdlib conflict

### Issue: Dashboard won't start

**Solution**: Run `uv sync --extra dashboard` then `make dash`

### Issue: JSON validation fails

**Solution**: Check JSON syntax and required fields per schema

## Project-Specific Rules

### File Naming

- Course codes in UPPERCASE (MATH221, not math221)
- JSON files in lowercase (schedule.json, not Schedule.json)
- Python modules in snake_case

### Git Workflow

- Never commit `build/` directory contents
- Always validate before committing course changes
- Dashboard state files (`dashboard/state/`) are Git-tracked

### Testing

- Run `make validate` before any build
- Test individual courses with `make course COURSE=<code>`
- Use `--ci` flag for scripts in CI/CD

## Security & Permissions

### Allowed Operations

- Edit any content, template, script, or dashboard file
- Run UV and Make commands
- Modify build outputs
- Update dashboard state

### Restricted Operations

- Direct modification of `uv.lock` (use `uv lock` instead)
- Editing `.env` file directly
- Git operations in `.git/` directory
- System-level package installation

## Performance Optimizations

### Build Speed

- UV caches packages for fast reinstalls
- Make targets use dependency tracking
- Parallel execution where possible

### Dashboard

- File locking prevents corruption
- Tasks loaded once per request
- Minimal JavaScript for fast loading

## Extended Context

### Academic Calendar

- Semester: August 25 - December 13, 2025
- Add/Drop deadline: September 5, 2025
- Withdrawal deadline: October 31, 2025
- Finals week: December 8-12, 2025

### Course Meeting Times

- MATH 221: MWF 8:00-8:50 AM
- MATH 251: MWF 9:00-9:50 AM
- STAT 253: TTh 10:00-11:15 AM

### Instructor Preferences

- Clean, minimal HTML output
- Mobile-friendly formatting
- Print-optimized stylesheets
- Consistent navigation structure

## Agentic Orchestration System (August 2025)

### Available Orchestration Patterns

#### Multi-Agent Workflows

- Use **Task tool** for spawning specialized subagents
- Prefix complex requests with **"think hard"** for deep analysis
- Use **"/semester-prep"** for complete semester preparation
- Use **"/agentic-debug"** for complex debugging workflows

#### Specialized Subagents

- **orchestrator**: Master coordinator (always start here for complex tasks)
- **qa-validator**: JSON validation, RSI compliance, date consistency
- **course-content**: Syllabus generation, schedule building, material creation
- **calendar-sync**: Date propagation, deadline management, conflict resolution
- **deploy-manager**: Site building, iframe setup, Cloudflare deployment
- **docs-keeper**: Documentation updates, decision tracking

#### Orchestration Commands

```bash
/semester-prep "Prepare Fall 2025 for launch"    # Complete preparation workflow
/agentic-debug "Fix MATH221 validation errors"   # Multi-agent debugging
/think hard about semester architecture          # Deep analysis with Opus
```

### Agent Coordination Patterns

#### Sequential Pipeline

User Request → qa-validator → course-content → calendar-sync → deploy-manager → docs-keeper

#### Parallel Execution

User Request → [MATH221 + MATH251 + STAT253] (simultaneously) → Merge Results

#### Quality Gates

Each phase includes validation checkpoints that must pass before proceeding to next phase

### TodoWrite Integration

The orchestrator automatically creates TodoWrite lists for complex workflows:

1. Breaks multi-step operations into trackable tasks
2. Assigns agents to specific tasks
3. Tracks progress through completion
4. Maintains context across agent handoffs

## Model-Specific Instructions

### For Quick Tasks (Haiku)

Focus on simple file edits, validation runs, and status checks

### For Standard Work (Sonnet)

Handle syllabus generation, dashboard updates, dependency management, and agent coordination

### For Architecture & Orchestration (Opus)

Design new features, refactor systems, solve complex integration issues, and coordinate multi-agent workflows

## Remember

1. **Always use UV** - Never use pip or venv directly
2. **Validate first** - Run validation before any build
3. **Use Make targets** - Leverage the Makefile for consistency
4. **Check dashboard state** - Tasks persist in `dashboard/state/`
5. **Test incrementally** - Build one course before building all
6. **Respect the calendar** - Week numbers and dates are authoritative
7. **Document changes** - Update this file when adding major features

## Quick Reference

```bash
# Daily workflow
make init          # Start of day
make validate      # Before changes
make all          # Full rebuild
make dash         # Launch dashboard

# Development
uv sync           # Update environment
uv run python    # Run any script
make help        # Show all targets

# Troubleshooting
make clean       # Remove build artifacts
uv sync --force  # Force dependency reinstall
make check-deps  # Verify system requirements
```

---
*Last updated: August 21, 2025 - UV migration complete, dashboard functional*
