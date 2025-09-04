# Fall 2025 Semester Course Management System - Project Brief

## Executive Summary

**Project Name:** Fall 2025 Semester Course Management System  
**Organization:** Kenai Peninsula College / University of Alaska Anchorage  
**Primary Purpose:** Automated generation and management of course materials for online mathematics and statistics courses  
**Architecture:** V2 Projection-based system with rule enforcement and CI/CD automation  
**Status:** Production-ready with successful Fall 2025 semester preparation completed  

## Project Overview

### Mission Statement
Provide a comprehensive, automated course management system that streamlines the creation, validation, and deployment of course materials while ensuring consistency, accessibility, and compliance with academic policies.

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
- **CI/CD:** GitHub Actions with automated validation and deployment
- **Deployment:** Cloudflare Pages (https://courses.jeffsthings.com)
- **Version Control:** Git with structured branch protection

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
  - One-click deployment to production
  - Real-time build monitoring
  - DOCX export capabilities
  - Git snapshot integration

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
  - `deploy-manager`: Production deployment and verification
- **Build Pipeline:** Make-based with dependency tracking
- **Validation:** Multi-layer validation (JSON schema, date rules, HTML structure)

### Quality Assurance
- **Testing Coverage:** 
  - Unit tests with 85%+ code coverage
  - Integration tests for full pipeline
  - Property-based testing for edge cases
  - Contract testing for date rules
  - Golden file testing for regression prevention
- **CI/CD Pipeline:**
  - Automated validation on every commit
  - Type checking with mypy --strict
  - Code formatting with Black and Ruff
  - Security scanning with Bandit

## Infrastructure & Deployment

### Development Environment
- **Prerequisites:** Python 3.13+, Git, Make, Pandoc (optional)
- **Setup:** `make init` for automatic environment configuration
- **Local Testing:** Flask development server with hot-reload

### Production Deployment
- **Primary URL:** https://courses.jeffsthings.com/
- **Fallback URL:** https://production.jeffsthings-courses.pages.dev/
- **Deployment Method:** 
  1. Dashboard one-click deploy (recommended)
  2. GitHub Actions on main branch push
  3. Manual wrangler deployment
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
├── .github/workflows/   # CI/CD pipelines (6 workflows)
├── site/               # Static site output for deployment
└── build/              # Generated artifacts (gitignored)
```

## Key Achievements

### Fall 2025 Preparation
- ✅ **100% Validation Rate:** All 44 JSON configuration files pass schema validation
- ✅ **167 Tasks Completed:** Full semester preparation via agent orchestration
- ✅ **Zero Weekend Due Dates:** Systematic enforcement across all courses
- ✅ **Production Deployment:** Live at courses.jeffsthings.com
- ✅ **LMS Integration:** Blackboard Ultra iframe compatibility verified

### Performance Metrics
- **Build Time:** < 5 seconds for full site generation
- **Test Suite:** < 30 seconds for complete test run
- **Deployment:** < 2 minutes from commit to production
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

## Future Roadmap

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

### Quantitative
- **Uptime:** 99.9% availability target
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

# Deployment
make deploy                     # Deploy to production
make deploy-staging            # Deploy to staging environment

# Development
make init                      # Initialize environment
make clean                     # Remove generated files
make docs                      # Download documentation
```

## License & Compliance

**Usage:** Educational use at Kenai Peninsula College / University of Alaska Anchorage  
**Repository:** https://github.com/jjohnson-47/semester-2025-fall  
**Deployment:** https://github.com/jjohnson-47/jeffsthings-courses (production)  
**Compliance:** FERPA compliant, ADA accessible, UAA IT policies  

---

*Last Updated: September 1, 2025*  
*Version: 2.0.0 (V2 Architecture)*  
*Status: Production Active*