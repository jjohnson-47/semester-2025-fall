# Documentation Index

## 📚 Overview

Complete documentation for the Fall 2025 Semester Course Management System.

## 📂 Documentation Structure

### Setup & Configuration

- [Quick Start Guide](../README.md#-quick-start) - Get up and running quickly
- [Installation Guide](../README.md#-development) - Detailed setup instructions
- [Environment Configuration](setup/environment.md) - Setting up your development environment
- [Claude Code Orchestration](../.claude-task-orchestration.md) - AI agent coordination system
- [Task Templates](../.claude-task-templates.md) - Ready-to-use agent task patterns
- [Orchestration Triggers](../.claude-orchestration-triggers.md) - Automatic agent coordination

### Reference Documentation

- [Dashboard Workflow Guide](reference/dashboard.md) - Complete dashboard system documentation
- [Course Information](reference/fall-2025-courses.md) - Course details, CRNs, and scheduling

### API Documentation

- [Build Scripts](api/scripts.md) - Python script documentation
- [Template System](api/templates.md) - Jinja2 template reference
- [JSON Schemas](api/schemas.md) - Data structure specifications

### Examples

- [Course Configuration Examples](examples/course-config.md) - Sample JSON configurations
- [Template Examples](examples/templates.md) - Custom template creation

### Archive

- [Legacy Documentation](archive/) - Previous versions and reference materials

## 🔍 Quick Reference

### File Locations

| Content Type | Location |
|-------------|----------|
| Course Data | `content/courses/[COURSE_CODE]/` |
| Templates | `templates/` |
| Build Scripts | `scripts/` |
| Dashboard | `dashboard/` |
| Generated Output | `build/` (gitignored) |

### Key Commands

```bash
# Traditional build commands
make all                    # Build everything
make dash                   # Start dashboard
make course COURSE=MATH221  # Build single course
make validate              # Validate configuration

# Claude Code Agent Commands (Task tool with subagent_type)
Task("Full system validation", subagent_type="qa-validator")
Task("Rebuild all course materials", subagent_type="course-content")
Task("Deploy to preview", subagent_type="deploy-manager")
Task("Update documentation", subagent_type="docs-keeper")
Task("Sync all calendars", subagent_type="calendar-sync")

# Multi-agent workflows with TodoWrite
TodoWrite + Task("Complete semester prep", subagent_type="qa-validator")
```

### Configuration Files

| File | Purpose |
|------|---------|
| `academic-calendar.json` | Semester calendar and dates |
| `profiles/instructor.json` | Instructor information |
| `variables/semester.json` | Semester configuration |
| `dashboard/state/courses.json` | Dashboard course configuration |
| `dashboard/state/tasks.json` | Current task states |
| `.claude-task-orchestration.md` | Claude Code agent coordination config |
| `.claude-task-templates.md` | Task templates for all agent types |
| `.claude-orchestration-triggers.md` | Automatic trigger patterns |

## 📝 Contributing to Documentation

When adding new documentation:

1. Place in appropriate subdirectory (`setup/`, `api/`, `examples/`)
2. Update this index with links
3. Use consistent markdown formatting
4. Include code examples where applicable
5. Cross-reference related documents

## 🔗 External Resources

- [Blackboard Ultra Documentation](https://help.blackboard.com/Learn/Instructor)
- [University of Alaska Academic Calendar](https://www.alaska.edu/academics/academic-calendar/)
- [KPC Faculty Resources](https://kpc.alaska.edu/faculty/)

---

*Last Updated: August 2025*
