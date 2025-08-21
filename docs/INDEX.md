# Documentation Index

## 📚 Overview
Complete documentation for the Fall 2025 Semester Course Management System.

## 📂 Documentation Structure

### Setup & Configuration
- [Quick Start Guide](../README.md#-quick-start) - Get up and running quickly
- [Installation Guide](../README.md#-development) - Detailed setup instructions
- [Environment Configuration](setup/environment.md) - Setting up your development environment

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
# Build everything
make all

# Start dashboard
make dash

# Build single course
make course COURSE=MATH221

# Validate configuration
make validate
```

### Configuration Files

| File | Purpose |
|------|---------|
| `academic-calendar.json` | Semester calendar and dates |
| `profiles/instructor.json` | Instructor information |
| `variables/semester.json` | Semester configuration |
| `dashboard/state/courses.json` | Dashboard course configuration |
| `dashboard/state/tasks.json` | Current task states |

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