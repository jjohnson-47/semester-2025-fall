# Architectural Evaluation Report: Course-as-Code Migration

**Date**: August 23, 2025
**Repository**: semester-2025-fall
**Evaluation Type**: Proposed Architecture Compatibility Assessment

## Executive Summary

The proposed "course-as-code" architecture represents a significant but achievable evolution of your existing system. Your current infrastructure already implements many foundational concepts (JSON-based content, Jinja2 templating, build automation), making this a **natural progression** rather than a complete rewrite. The migration path is clear, with primary challenges around restructuring data organization and adding new tooling layers.

## Current State Analysis

### Strengths Already in Place

- **JSON-driven content model** with per-course data files in `content/courses/`
- **Jinja2 templating system** for syllabi and schedules (`templates/*.j2`)
- **Make-based build orchestration** with course-specific targets
- **Task management dashboard** with smart prioritization (Flask-based at port 5055)
- **Strong validation layer** using JSON Schema (`scripts/validate_json.py`)
- **UV package management** for modern Python dependency handling
- **Flask-based web interface** ready for serving static content

### Current Repository Structure

```
semester-2025-fall/
├── content/courses/         # Course-specific JSON data
│   ├── MATH221/
│   ├── MATH251/
│   └── STAT253/
├── dashboard/               # Task management system
│   ├── app.py              # Flask application
│   ├── state/              # Task and course state
│   └── tools/              # Priority engine
├── scripts/                # Build automation
├── templates/              # Jinja2 templates
├── build/                  # Generated outputs
└── Makefile               # Build orchestration
```

### Architectural Gaps to Address

1. **Deduplication enforcement** - No current mechanism to prevent content duplication
2. **Global content management** - Policies/snippets scattered, not centralized
3. **GitHub Pages deployment** - No CI/CD workflow configured (`.github/` directory absent)
4. **Blackboard iframe compatibility** - Not tested/validated
5. **Hierarchical variable system** - Single-level configuration currently

## Compatibility Assessment

### High Compatibility (Minimal Changes)

- ✅ **Jinja2 templating** - Direct reuse with enhanced partials
- ✅ **JSON data model** - Restructure paths, maintain format
- ✅ **Make build system** - Extend existing targets
- ✅ **Python scripts** - Refactor for new directory structure
- ✅ **Task dashboard** - Update paths in config
- ✅ **Validation framework** - Extend schemas for new structures

### Moderate Adaptation Required

- ⚠️ **Content organization** - Migrate to `content/global/` hierarchy
- ⚠️ **Variable layering** - Add `static.json`, `annual.2025.json` to existing `variables/`
- ⚠️ **Schema validation** - Expand to cover new data shapes
- ⚠️ **Build output** - Redirect to `site/` for Pages deployment

### New Components Needed

- 🆕 **Deduplication checker** (`scripts/check_dedupe.py`)
- 🆕 **GitHub Actions workflow** (`.github/workflows/pages.yml`)
- 🆕 **Blackboard export tool** (`scripts/export_blackboard.py`)
- 🆕 **Content fingerprinting** for duplicate detection
- 🆕 **Stable URL mapping** system

## Integration Considerations

### 1. Dashboard Integration

Your sophisticated task management system (with smart prioritization, Now Queue, and chain analysis) needs minimal updates:

```python
# Update paths in dashboard/config.py
CONTENT_DIR = Path("content/courses")  # → stays same
BUILD_DIR = Path("site")               # → change from "build"
GLOBAL_DIR = Path("content/global")    # → new addition
TEMPLATES_DIR = Path("templates/partials")  # → for includes
```

The dashboard's existing features remain intact:

- Smart prioritization with `reprioritize.py`
- Task dependency tracking
- Now Queue generation
- Phase-aware scheduling

### 2. Build Pipeline Evolution

Enhance existing Makefile targets:

```make
# Existing target enhancement
syllabi: calendar dedupe-check
    @mkdir -p site/courses/$(COURSE)/syllabi
    @$(PYTHON) scripts/build_syllabi.py --out site/

# New validation layer
dedupe-check:
    @$(PYTHON) scripts/check_dedupe.py || exit 1

# New publishing target
publish-pages: build
    @echo "Deploying to GitHub Pages..."
    @gh workflow run pages.yml
```

### 3. Template Refactoring Strategy

Transform from embedded content to included partials:

```jinja2
{# Current approach in templates/syllabus.html.j2 #}
<div class="policies">{{ course.class_policies }}</div>

{# New approach with partials #}
{% include "partials/policies/academic_integrity.html.j2" %}
{% include "partials/policies/grading.html.j2" with context %}
```

## Structural Issues to Address

### 1. Content Deduplication Process

**Current State**: Each course has separate JSON files with potentially duplicate content:

- `MATH221/class_policies.json`
- `MATH251/class_policies.json`
- `STAT253/class_policies.json`

**Solution Architecture**:

```
content/
├── global/
│   ├── policies/
│   │   ├── academic_integrity.json
│   │   ├── accessibility.json
│   │   └── late_work.json
│   └── snippets/
│       └── footer.html.j2
└── courses/
    └── MATH221/
        └── overrides/  # Course-specific variations only
```

### 2. URL Stability Contract

**Current**: No formal URL structure
**Proposed**: Implement predictable hierarchy with redirects

```
site/
├── courses/
│   ├── MATH221/
│   │   ├── fall-2025/
│   │   │   ├── syllabus/index.html
│   │   │   └── schedule/index.html
│   │   └── latest → fall-2025/  # Symlink
│   └── index.html  # Course directory
└── index.html  # Site root
```

### 3. Cross-Reference Management

**Current**: Informal references between documents
**Solution**: Canonical ID system integrated with existing task IDs

```json
{
  "id": "page:math221:syllabus",
  "course": "MATH221",
  "type": "syllabus",
  "url": "/courses/MATH221/fall-2025/syllabus/",
  "dependencies": ["data:math221:description", "global:policies:grading"]
}
```

### 4. Task System Integration

Leverage existing task infrastructure for migration:

```python
# dashboard/templates_src/migration_tasks.yaml
templates:
  - id: "migrate:extract-policies"
    title: "Extract global policies from course files"
    category: "migration"
    priority: "high"

  - id: "migrate:setup-github-pages"
    title: "Configure GitHub Pages workflow"
    depends_on: ["migrate:extract-policies"]

  - id: "migrate:test-blackboard"
    title: "Test Blackboard iframe embedding"
    milestone: true
```

## Tooling Considerations

### Required New Dependencies

```toml
# pyproject.toml additions
[project.dependencies]
# Existing dependencies preserved
jinja2 = ">=3.1.2"
pyyaml = ">=6.0"
jsonschema = ">=4.17.3"
flask = ">=3.1.2"

# New additions for course-as-code
pydantic = ">=2.0"       # Enhanced schema validation
minify-html = ">=0.11"   # Site optimization
python-frontmatter = ">=1.0"  # Markdown metadata
```

### GitHub Actions Requirements

Create `.github/workflows/pages.yml`:

```yaml
name: Build & Deploy Pages
on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv sync
      - run: make validate
      - run: make dedupe-check
      - run: make build-site
      - uses: actions/upload-pages-artifact@v3
        with:
          path: 'site'

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - uses: actions/deploy-pages@v4
```

### Blackboard Compatibility Testing

```bash
# Local iframe test server with CORS headers
cat > test_server.py << 'EOF'
from flask import Flask, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=["https://blackboard.alaska.edu"])

@app.route('/<path:path>')
def serve(path):
    response = send_from_directory('site', path)
    response.headers['X-Frame-Options'] = 'ALLOWALL'
    return response

if __name__ == '__main__':
    app.run(port=8000, debug=True)
EOF

uv run python test_server.py
```

## Risk Assessment

### Low Risk

- Build system modifications (extending existing Make targets)
- Template refactoring (Jinja2 includes are standard)
- Directory restructuring (scripted migration)
- Dashboard path updates (configuration change)

### Medium Risk

- **GitHub Pages iframe blocking**
  - *Mitigation*: Cloudflare Pages fallback prepared
  - *Testing*: Early iframe validation
- **Dashboard state migration**
  - *Mitigation*: Parallel operation during transition
- **URL breaking changes**
  - *Mitigation*: Redirect rules and `latest/` symlinks

### High Risk

- **Blackboard CSP restrictions**
  - *Impact*: Complete iframe blocking
  - *Mitigation*: Requires external hosting with header control
  - *Fallback*: Direct links with "Open in new tab" option

## Migration Roadmap

### Phase 1: Foundation (Days 1-3)

1. Create directory structure

   ```bash
   mkdir -p content/global/{policies,tech,snippets}
   mkdir -p .github/workflows
   mkdir -p site
   ```

2. Implement deduplication checker
3. Set up GitHub Actions workflow
4. Test basic Pages deployment

### Phase 2: Content Migration (Days 4-7)

1. Extract shared policies using existing JSON structure
2. Refactor templates to use includes
3. Update build scripts for `site/` output
4. Run existing test suite for validation

### Phase 3: Integration (Week 2)

1. Update dashboard configuration

   ```python
   # dashboard/config.py changes
   BUILD_DIR = Path("site")
   GLOBAL_CONTENT = Path("content/global")
   ```

2. Test Blackboard iframe embedding
3. Implement Cloudflare Pages fallback if needed
4. Document URL structure

### Phase 4: Optimization (Week 3)

1. Add content fingerprinting
2. Implement `latest/` symlinks
3. Set up redirect rules
4. Performance testing with your existing dashboard metrics

## Specific Recommendations

### 1. Leverage Existing Infrastructure

Your current system's strengths map directly to the new architecture:

- **Task dashboard** → Migration task tracking
- **JSON validation** → Schema evolution
- **Make targets** → Extended build pipeline
- **Flask app** → Preview server for testing

### 2. Implement Progressive Enhancement

```bash
# Run both pipelines in parallel initially
make all                    # Current system → build/
make build-site            # New system → site/
make compare-outputs       # Validation tool
```

### 3. Use Task System for Migration

```python
# Generate migration tasks
python dashboard/tools/generate_tasks.py \
  --template dashboard/templates_src/migration_tasks.yaml \
  --out dashboard/state/migration_tasks.json

# Track via existing dashboard
make dash  # View migration progress at :5055
```

### 4. Early Blackboard Validation

```html
<!-- Test embed immediately with your CRNs -->
<iframe
  src="https://jjohnson-47.github.io/semester-2025-fall/courses/MATH221/syllabus/"
  width="100%"
  height="1100">
</iframe>
```

## Compatibility Matrix

| Component | Current State | Required Changes | Risk Level | Priority |
|-----------|--------------|------------------|------------|----------|
| JSON Data Model | ✅ Fully compatible | Path reorganization | Low | High |
| Jinja2 Templates | ✅ Compatible | Add partials/includes | Low | High |
| Task Dashboard | ✅ Compatible | Config updates | Low | Medium |
| Build System | ✅ Make-based | New targets | Low | High |
| Validation | ✅ JSON Schema | Extend schemas | Low | Medium |
| CI/CD | ❌ Not present | Create workflows | Medium | High |
| URL Structure | ⚠️ Informal | Formalize | Medium | High |
| Deduplication | ❌ Not enforced | New tooling | Low | High |
| Blackboard | ❓ Untested | Validate early | High | Critical |

## Conclusion

The proposed "course-as-code" architecture is **highly compatible** with your existing semester-2025-fall system. Your strong foundation provides excellent building blocks:

1. **Existing JSON-driven content** maps directly to the new structure
2. **Jinja2 templating** supports the partial/include pattern natively
3. **Task dashboard** can track and prioritize migration work
4. **Make-based builds** extend naturally to new targets
5. **Validation framework** adapts to new schemas

The primary challenges are organizational rather than technical. The migration represents an evolutionary improvement that:

- Eliminates content duplication through `content/global/`
- Enables GitHub Pages hosting with proper CI/CD
- Maintains your sophisticated task management system
- Preserves all existing workflows and tools
- Adds systematic deduplication and URL stability

**Final Recommendation**: Proceed with confidence. Your existing infrastructure provides an excellent foundation. Start with Phase 1 (Foundation) to validate GitHub Pages compatibility while maintaining parallel systems. The incremental migration path ensures zero disruption to your Fall 2025 semester preparation.

## Appendix: Quick Start Commands

```bash
# 1. Create new structure
mkdir -p content/global/{policies,tech,snippets,people}
mkdir -p .github/workflows
mkdir -p site

# 2. Test GitHub Pages locally
make build-site
cd site && python -m http.server 8000

# 3. Generate migration tasks
python dashboard/tools/generate_tasks.py \
  --template migration_template.yaml

# 4. Track progress
make dash  # Monitor at http://127.0.0.1:5055

# 5. Validate continuously
make validate && make dedupe-check
```

---
*Generated: August 23, 2025*
*Repository: jjohnson-47/semester-2025-fall*
*Evaluation requested for: Course-as-Code Architecture Migration*
