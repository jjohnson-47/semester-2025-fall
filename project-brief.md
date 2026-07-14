# Fall 2025 Semester Course Management System - Project Brief

> **Current posture (2026-07-14): retained public archive.** The Fall 2025
> teaching term is complete. Local validation and archive generation remain
> supported, but automatic publication, scheduled maintenance, and dashboard
> deployment controls are retired. See
> [`docs/adr/0005-retained-public-archive.md`](docs/adr/0005-retained-public-archive.md).

## Executive Summary

**Project Name:** Fall 2025 Semester Course Management System  
**Organization:** Kenai Peninsula College / University of Alaska Anchorage  
**Primary Purpose:** Preserve the source and reproducible generation of Fall 2025 mathematics and statistics course materials
**Architecture:** V2 projection-based system with rule enforcement and CI validation
**Status:** Course taught; retained public archive with publication operations retired

## Project Overview

### Mission Statement
Preserve the completed Fall 2025 course system, its source materials, and a reproducible local build while retaining the published site as a public teaching archive.

### Key Objectives
- **Automation:** Eliminate manual course material generation through template-based systems
- **Consistency:** Enforce uniform policies across all courses (e.g., no weekend due dates)
- **Scalability:** Support multiple courses with minimal configuration overhead
- **Accessibility:** Generate iframe-compatible materials for Blackboard Ultra LMS integration
- **Reliability:** Maintain 100% validation pass rate with comprehensive testing

## Technical Architecture

### Core Technology Stack
- **Language:** Python 3.13+ 
- **Package Manager:** UV (v0.8.14+)
- **Build System:** GNU Make 4.4.1 with BUILD_MODE=v2
- **Web Framework:** Flask 3.1.2+ with Jinja2 templating
- **Testing:** Pytest 7.4.0+ with property-based testing via Hypothesis
- **CI:** GitHub Actions for validation; automatic publication is retired
- **Public Archive:** Cloudflare Pages at https://courses.jeffsthings.com
- **Version Control:** Git with a PR-based working convention; `main` was not protected at the 2026-07-14 audit

### V2 Architecture Components

#### 1. Projection System
- **Location:** `scripts/services/projection_adapter.py`
- **Purpose:** Transform course data into purpose-specific views
- **Features:**
  - Schema v1.1.0 compliance with stable IDs
  - Full provenance tracking for all transformations
  - Context-aware rendering for different output formats

#### 2. Rules Engine
- **Location:** `scripts/rules/`
- **Key Rules:**
  - No weekend due dates (automatic adjustment to Friday/Monday)
  - Date consistency across all course materials
  - Schema validation at build time
- **Implementation:** `CourseRulesEngine` with `DateRules` enforcement

#### 3. Style System
- **Location:** `scripts/utils/style_system.py`
- **Course Themes:**
  - MATH221: Blue (#0066cc)
  - MATH251: Green (#006600)
  - STAT253: Orange (#cc6600)
- **Features:** Embedded CSS for standalone viewing and iframe compatibility

#### 4. Task Management Dashboard
- **URL:** http://localhost:5055
- **Features:**
  - AI-driven task prioritization
  - Real-time build monitoring
  - DOCX export capabilities
  - Git snapshot integration
- **Archive Boundary:** Local management and inspection only; deployment controls are retired

## Course Portfolio

### Managed Courses (Fall 2025)

| Course | Title | CRN | Credits | Format | Enrollment |
|--------|-------|-----|---------|---------|------------|
| **MATH 221** | Applied Calculus for Managerial & Social Sciences | 74645 | 3 | Online Async | RW1 Section |
| **MATH 251** | Calculus I | 74647 | 4 | Online Async | RW1 Section |
| **STAT 253** | Applied Statistics for the Sciences | 74688 | 4 | Online Async | RW1 Section |

### Academic Calendar
- **Semester Duration:** August 25 - December 13, 2025
- **Add/Drop Deadline:** September 5, 2025
- **Withdrawal Deadline:** October 31, 2025
- **Finals Week:** December 8-13, 2025
- **Key Holidays:** Labor Day (Sep 1), Fall Break (Nov 27-28)

## System Capabilities

### Content Generation
- **Syllabi:** HTML/Markdown with embedded styling and print optimization
- **Schedules:** Week-by-week course plans with automated date calculation
- **Blackboard Packages:** LMS-ready content with proper formatting
- **Interactive Tools:** Epsilon-delta visualizations for calculus concepts

### Automation Features
- **Agent Orchestration:** Specialized agents for different workflow stages
  - `qa-validator`: JSON validation and schema compliance
  - `course-content`: Material generation and formatting
  - `calendar-sync`: Date propagation and conflict resolution
- **Build Pipeline:** Make-based with dependency tracking
- **Validation:** Multi-layer validation (JSON schema, date rules, HTML structure)

### Quality Assurance
- **Testing Coverage:** 
  - Unit tests with 85%+ code coverage
  - Integration tests for full pipeline
  - Property-based testing for edge cases
  - Contract testing for date rules
  - Golden file testing for regression prevention
- **CI Pipeline:**
  - Automated validation on every commit
  - Type checking with mypy --strict
  - Code formatting with Black and Ruff
  - Security scanning with Bandit

## Archive Infrastructure

### Development Environment
- **Prerequisites:** Python 3.13+, Git, Make, Pandoc (optional)
- **Setup:** `make init` for automatic environment configuration
- **Local Testing:** Flask development server with hot-reload

### Retained Public Archive
- **Primary URL:** https://courses.jeffsthings.com/
- **Fallback URL:** https://production.jeffsthings-courses.pages.dev/
- **Publication State:** The existing site may remain available, but repository changes do not publish automatically
- **Local Rebuild:** `BUILD_MODE=v2 make build-site ENV=preview`
- **Reactivation:** Requires a new owner decision and the controls in ADR 0005
- **CDN:** Cloudflare Pages with global distribution
- **SSL/TLS:** Automatic certificate management

### Security & Compliance
- **CSP Headers:** Configured for iframe embedding in Blackboard Ultra
- **Authentication:** Instructor credentials via UAA SSO
- **Data Protection:** No student PII stored in repository
- **Secret Management:** Gopass integration for API keys

## Project Structure

```
semester-2025-fall/
├── content/courses/      # Course JSON configuration (source of truth)
│   ├── MATH221/         # 14 JSON files per course
│   ├── MATH251/         
│   └── STAT253/         
├── scripts/             # Build and automation scripts
│   ├── services/        # V2 CourseService, ValidationGateway
│   ├── rules/           # Business logic enforcement
│   ├── utils/           # Shared utilities and helpers
│   └── builders/        # Projection adapters
├── dashboard/           # Flask task management application
│   ├── agents/          # Specialized automation agents (7 types)
│   ├── api/             # RESTful endpoints
│   ├── templates/       # UI templates
│   └── state/           # Task persistence
├── templates/           # Jinja2 templates for content
├── tests/               # Comprehensive test suite
│   ├── contracts/       # Business rule validation
│   ├── integration/     # End-to-end testing
│   ├── property/        # Hypothesis-based testing
│   └── golden/          # Regression testing
├── .github/workflows/   # Validation and release workflows
├── site/               # Retained static archive output
└── build/              # Generated artifacts (gitignored)
```

## Key Achievements

### Fall 2025 Preparation
- ✅ **100% Validation Rate:** All 44 JSON configuration files pass schema validation
- ✅ **167 Tasks Completed:** Full semester preparation via agent orchestration
- ✅ **Zero Weekend Due Dates:** Systematic enforcement across all courses
- ✅ **Public Archive:** Completed teaching output retained at courses.jeffsthings.com
- ✅ **LMS Integration:** Blackboard Ultra iframe compatibility verified

### Performance Metrics
- **Build Time:** < 5 seconds for full site generation
- **Test Suite:** < 30 seconds for complete test run
- **Dashboard Load:** < 200ms response time
- **Validation:** Real-time with < 100ms feedback

## Innovation Highlights

### Interactive Educational Tools
- **Epsilon-Delta Visualizer:** Interactive tool for teaching limits in Calculus
  - Learn, Practice, and Challenge modes
  - Real-time graph visualization
  - KaTeX mathematical rendering
  - Progress tracking and gamification

### Smart Task Prioritization
- **AI-Driven Queue:** Identifies highest-impact tasks
- **Chain Analysis:** Detects task dependencies and blockers
- **Phase Awareness:** Adjusts priorities based on semester timeline
- **Unblock Metrics:** Shows downstream impact of each task

### Projection-Based Architecture
- **Data Transformation:** Single source of truth with multiple views
- **Rule Application:** Centralized business logic enforcement
- **Template Simplification:** Clean separation of data and presentation
- **Provenance Tracking:** Complete audit trail for all changes

## Historical Roadmap

The items below were planning ideas during active development. They are not
current commitments for this retired semester repository; any reactivation or
new-semester work requires a separate owner decision.

### Near-term (Q1 2026)
- [ ] Spring 2026 semester preparation
- [ ] Additional interactive tools for statistics
- [ ] Enhanced mobile responsiveness
- [ ] Student progress tracking integration

### Long-term Vision
- [ ] Multi-instructor support
- [ ] Real-time collaboration features
- [ ] AI-powered content suggestions
- [ ] Automated grading integration
- [ ] Analytics dashboard for learning insights

## Success Metrics

### Quantitative (Active-Semester Targets)
- **Error Rate:** < 0.1% build failures
- **Coverage:** 85%+ test coverage maintained
- **Validation:** 100% schema compliance

### Qualitative
- **Instructor Efficiency:** 80% reduction in course setup time
- **Student Satisfaction:** Consistent, accessible course materials
- **Maintainability:** Clear documentation and modular architecture
- **Scalability:** Easy addition of new courses and features

## Team & Contact

**Lead Developer/Instructor:** Jeffrey Johnson  
**Email:** jjohnson47@alaska.edu  
**Institution:** Kenai Peninsula College  
**Department:** Mathematics and Statistics  
**Office:** Ward Building, Soldotna Campus  

## Technical Documentation

### Essential References
- **README.md** - Project setup and quick start guide
- **CLAUDE.md** - AI assistant configuration and patterns
- **docs/adr/** - Architecture Decision Records
- **dashboard/API_DOCUMENTATION.md** - Complete API reference
- **docs/INTERACTIVE_TOOLS_GUIDE.md** - Interactive tool development

### Command Reference
```bash
# Core Operations (always use BUILD_MODE=v2)
BUILD_MODE=v2 make all          # Build everything
BUILD_MODE=v2 make validate     # Validate JSON schemas
BUILD_MODE=v2 make test         # Run test suite
BUILD_MODE=v2 make dash         # Start dashboard

# Retained archive verification (local only)
BUILD_MODE=v2 make build-site ENV=preview
test -f site/manifest.json
test -f site/_headers

# Development
make init                      # Initialize environment
make clean                     # Remove generated files
make docs                      # Download documentation
```

## License & Compliance

**Usage:** Educational use at Kenai Peninsula College / University of Alaska Anchorage  
**Repository:** https://github.com/jjohnson-47/semester-2025-fall  
**Public Archive:** https://courses.jeffsthings.com/
**Compliance:** FERPA compliant, ADA accessible, UAA IT policies  

---

*Last Updated: July 14, 2026*
*Version: 2.0.0 (V2 Architecture)*  
*Status: Retained Public Archive; Publication Retired*
