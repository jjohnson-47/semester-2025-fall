#!/usr/bin/env bash
# Comprehensive documentation fetcher for Fall 2025 project
# Downloads latest/stable versions of all relevant documentation
# Organized for AI agent accessibility and easy reference
set -euo pipefail

# Configuration
DOCS_ROOT="${DOCS_DIR:-docs/reference}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
LOG_FILE="$DOCS_ROOT/fetch_log_${TIMESTAMP}.txt"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create directory structure
mkdir -p "$DOCS_ROOT"/{python,flask,frontend,tools,standards}

# Logging function
log() {
    echo -e "${GREEN}[$(date +%H:%M:%S)]${NC} $1"
    echo "[$(date +%Y-%m-%d_%H:%M:%S)] $1" >> "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    echo "[ERROR] $1" >> "$LOG_FILE"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
    echo "[INFO] $1" >> "$LOG_FILE"
}

# Fetch function with retry logic
fetch_doc() {
    local url="$1"
    local category="$2"
    local name="$3"
    local retries=3
    
    info "Fetching $name from $url"
    
    # Create category directory
    mkdir -p "$DOCS_ROOT/$category/$name"
    
    # Try fetching with retries
    for i in $(seq 1 $retries); do
        if curl -sS --max-time 30 \
            -H "User-Agent: Mozilla/5.0 Documentation Fetcher" \
            -L "$url" \
            -o "$DOCS_ROOT/$category/$name/index.html" 2>/dev/null; then
            log "✓ Downloaded $name"
            return 0
        else
            if [ $i -lt $retries ]; then
                error "Failed attempt $i for $name, retrying..."
                sleep 2
            fi
        fi
    done
    
    error "Failed to download $name after $retries attempts"
    return 1
}

# Fetch with wget for full page resources
fetch_page_complete() {
    local url="$1"
    local category="$2"
    local name="$3"
    
    info "Fetching complete page: $name"
    mkdir -p "$DOCS_ROOT/$category/$name"
    
    wget --quiet \
        --tries=3 \
        --timeout=30 \
        --convert-links \
        --page-requisites \
        --no-parent \
        --directory-prefix="$DOCS_ROOT/$category/$name" \
        --user-agent="Mozilla/5.0 Documentation Fetcher" \
        "$url" 2>/dev/null || {
        error "Failed to fetch complete page: $name"
        return 1
    }
    
    log "✓ Downloaded complete page: $name"
}

# =====================================
# PYTHON 3.13 DOCUMENTATION
# =====================================

log "Starting Python 3.13 documentation download..."

# Core Python 3.13 docs
fetch_doc "https://docs.python.org/3.13/library/index.html" "python" "stdlib"
fetch_doc "https://docs.python.org/3.13/library/typing.html" "python" "typing"
fetch_doc "https://docs.python.org/3.13/library/asyncio.html" "python" "asyncio"
fetch_doc "https://docs.python.org/3.13/library/pathlib.html" "python" "pathlib"
fetch_doc "https://docs.python.org/3.13/library/json.html" "python" "json"
fetch_doc "https://docs.python.org/3.13/library/datetime.html" "python" "datetime"
fetch_doc "https://docs.python.org/3.13/library/logging.html" "python" "logging"
fetch_doc "https://docs.python.org/3.13/library/unittest.html" "python" "unittest"
fetch_doc "https://docs.python.org/3.13/whatsnew/3.13.html" "python" "whatsnew"

# =====================================
# FLASK 3.x AND ECOSYSTEM
# =====================================

log "Starting Flask ecosystem documentation download..."

# Flask 3.x (latest stable)
fetch_doc "https://flask.palletsprojects.com/en/stable/" "flask" "core"
fetch_doc "https://flask.palletsprojects.com/en/stable/quickstart/" "flask" "quickstart"
fetch_doc "https://flask.palletsprojects.com/en/stable/tutorial/" "flask" "tutorial"
fetch_doc "https://flask.palletsprojects.com/en/stable/blueprints/" "flask" "blueprints"
fetch_doc "https://flask.palletsprojects.com/en/stable/config/" "flask" "config"
fetch_doc "https://flask.palletsprojects.com/en/stable/testing/" "flask" "testing"
fetch_doc "https://flask.palletsprojects.com/en/stable/errorhandling/" "flask" "errorhandling"
fetch_doc "https://flask.palletsprojects.com/en/stable/cli/" "flask" "cli"
fetch_doc "https://flask.palletsprojects.com/en/stable/server/" "flask" "server"
fetch_doc "https://flask.palletsprojects.com/en/stable/patterns/" "flask" "patterns"
fetch_doc "https://flask.palletsprojects.com/en/stable/deploying/" "flask" "deploying"
fetch_doc "https://flask.palletsprojects.com/en/stable/async/" "flask" "async"
fetch_doc "https://flask.palletsprojects.com/en/stable/api/" "flask" "api"

# Jinja2 3.x (latest)
fetch_doc "https://jinja.palletsprojects.com/en/stable/" "flask" "jinja2"
fetch_doc "https://jinja.palletsprojects.com/en/stable/templates/" "flask" "jinja2-templates"
fetch_doc "https://jinja.palletsprojects.com/en/stable/api/" "flask" "jinja2-api"

# Werkzeug 3.x (latest)
fetch_doc "https://werkzeug.palletsprojects.com/en/stable/" "flask" "werkzeug"

# Click 8.x (latest)
fetch_doc "https://click.palletsprojects.com/en/stable/" "flask" "click"

# Flask extensions (latest versions)
fetch_doc "https://flask-cors.readthedocs.io/en/latest/" "flask" "flask-cors"
fetch_doc "https://flask-limiter.readthedocs.io/en/stable/" "flask" "flask-limiter"
fetch_doc "https://pythonhosted.org/Flask-Caching/" "flask" "flask-caching"

# =====================================
# FRONTEND TECHNOLOGIES (LATEST)
# =====================================

log "Starting frontend documentation download..."

# HTMX 2.x (latest)
fetch_doc "https://htmx.org/docs/" "frontend" "htmx"
fetch_doc "https://htmx.org/attributes/hx-get/" "frontend" "htmx-get"
fetch_doc "https://htmx.org/attributes/hx-post/" "frontend" "htmx-post"
fetch_doc "https://htmx.org/attributes/hx-target/" "frontend" "htmx-target"
fetch_doc "https://htmx.org/attributes/hx-swap/" "frontend" "htmx-swap"
fetch_doc "https://htmx.org/attributes/hx-trigger/" "frontend" "htmx-trigger"
fetch_doc "https://htmx.org/attributes/hx-swap-oob/" "frontend" "htmx-swap-oob"

# Alpine.js 3.x (latest)
fetch_doc "https://alpinejs.dev/start-here" "frontend" "alpine-start"
fetch_doc "https://alpinejs.dev/essentials/installation" "frontend" "alpine-install"
fetch_doc "https://alpinejs.dev/essentials/state" "frontend" "alpine-state"
fetch_doc "https://alpinejs.dev/essentials/events" "frontend" "alpine-events"
fetch_doc "https://alpinejs.dev/directives/on" "frontend" "alpine-on"
fetch_doc "https://alpinejs.dev/directives/data" "frontend" "alpine-data"
fetch_doc "https://alpinejs.dev/upgrade-guide" "frontend" "alpine-upgrade"

# Tailwind CSS 3.x (latest)
fetch_doc "https://tailwindcss.com/docs/installation" "frontend" "tailwind-install"
fetch_doc "https://tailwindcss.com/docs/utility-first" "frontend" "tailwind-utility"
fetch_doc "https://tailwindcss.com/docs/responsive-design" "frontend" "tailwind-responsive"
fetch_doc "https://tailwindcss.com/docs/dark-mode" "frontend" "tailwind-dark"
fetch_doc "https://tailwindcss.com/docs/customizing-colors" "frontend" "tailwind-colors"

# =====================================
# TOOLS AND LIBRARIES (LATEST)
# =====================================

log "Starting tools documentation download..."

# pytest 8.x (latest)
fetch_doc "https://docs.pytest.org/en/stable/" "tools" "pytest"
fetch_doc "https://docs.pytest.org/en/stable/how-to/fixtures.html" "tools" "pytest-fixtures"
fetch_doc "https://docs.pytest.org/en/stable/how-to/mark.html" "tools" "pytest-markers"
fetch_doc "https://docs.pytest.org/en/stable/how-to/parametrize.html" "tools" "pytest-parametrize"

# UV (latest) - Modern Python package manager
fetch_doc "https://docs.astral.sh/uv/" "tools" "uv"
fetch_doc "https://docs.astral.sh/uv/getting-started/" "tools" "uv-start"
fetch_doc "https://docs.astral.sh/uv/concepts/projects/" "tools" "uv-projects"

# Ruff (latest) - Fast Python linter
fetch_doc "https://docs.astral.sh/ruff/" "tools" "ruff"
fetch_doc "https://docs.astral.sh/ruff/configuration/" "tools" "ruff-config"

# Black (latest) - Python formatter
fetch_doc "https://black.readthedocs.io/en/stable/" "tools" "black"

# JSON Schema (latest spec)
fetch_doc "https://json-schema.org/specification" "tools" "json-schema-spec"
fetch_doc "https://json-schema.org/understanding-json-schema/" "tools" "json-schema-guide"
fetch_doc "https://python-jsonschema.readthedocs.io/en/stable/" "tools" "python-jsonschema"

# PyYAML 6.x (latest)
fetch_doc "https://pyyaml.org/wiki/PyYAMLDocumentation" "tools" "pyyaml"

# =====================================
# WEB STANDARDS AND ACCESSIBILITY
# =====================================

log "Starting standards documentation download..."

# Web Accessibility
fetch_doc "https://www.w3.org/WAI/ARIA/apg/" "standards" "aria-apg"
fetch_doc "https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/" "standards" "aria-modal"
fetch_doc "https://www.w3.org/WAI/WCAG22/quickref/" "standards" "wcag22"

# MDN Web Docs
fetch_doc "https://developer.mozilla.org/en-US/docs/Web/HTML/Element/dialog" "standards" "html-dialog"
fetch_doc "https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API" "standards" "fetch-api"
fetch_doc "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Modules" "standards" "js-modules"

# HTTP/REST Standards
fetch_doc "https://developer.mozilla.org/en-US/docs/Web/HTTP/Status" "standards" "http-status"
fetch_doc "https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods" "standards" "http-methods"
fetch_doc "https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers" "standards" "http-headers"

# =====================================
# CREATE DOCUMENTATION INDEX
# =====================================

log "Creating documentation index..."

cat > "$DOCS_ROOT/INDEX.md" << 'EOF'
# Project Documentation Reference Library

## Overview
This is a comprehensive collection of documentation for all technologies used in the Fall 2025 semester project.
All documentation reflects the latest stable versions as of the download date.

## Quick Navigation

### 🐍 Python 3.13
- [Standard Library](python/stdlib/index.html) - Complete Python 3.13 standard library reference
- [Typing](python/typing/index.html) - Type hints and static typing
- [AsyncIO](python/asyncio/index.html) - Asynchronous I/O
- [Pathlib](python/pathlib/index.html) - Object-oriented filesystem paths
- [What's New in 3.13](python/whatsnew/index.html) - Latest Python features

### 🌶️ Flask Ecosystem (3.x)
- [Flask Core](flask/core/index.html) - Main Flask documentation
- [Quick Start](flask/quickstart/index.html) - Getting started guide
- [Blueprints](flask/blueprints/index.html) - Application modularity
- [Configuration](flask/config/index.html) - Configuration handling
- [Testing](flask/testing/index.html) - Testing Flask applications
- [Patterns](flask/patterns/index.html) - Common patterns and best practices
- [API Reference](flask/api/index.html) - Complete API documentation
- [Jinja2 Templates](flask/jinja2/index.html) - Template engine
- [Werkzeug](flask/werkzeug/index.html) - WSGI utilities
- [Click](flask/click/index.html) - Command line interface

### 🎨 Frontend Technologies
- [HTMX](frontend/htmx/index.html) - Hypermedia-driven applications
- [Alpine.js](frontend/alpine-start/index.html) - Minimal reactive framework
- [Tailwind CSS](frontend/tailwind-install/index.html) - Utility-first CSS

### 🛠️ Development Tools
- [pytest](tools/pytest/index.html) - Testing framework
- [UV](tools/uv/index.html) - Modern Python package manager
- [Ruff](tools/ruff/index.html) - Fast Python linter
- [Black](tools/black/index.html) - Code formatter
- [JSON Schema](tools/json-schema-spec/index.html) - Data validation
- [PyYAML](tools/pyyaml/index.html) - YAML parser

### 📐 Standards & Best Practices
- [ARIA APG](standards/aria-apg/index.html) - Accessibility patterns
- [WCAG 2.2](standards/wcag22/index.html) - Web accessibility guidelines
- [HTTP Methods](standards/http-methods/index.html) - RESTful API design
- [HTTP Status Codes](standards/http-status/index.html) - Response codes

## Version Information
- **Python**: 3.13.6
- **Flask**: 3.x (latest stable)
- **Jinja2**: 3.x
- **pytest**: 8.x
- **HTMX**: 2.x
- **Alpine.js**: 3.x
- **Tailwind CSS**: 3.x

## Usage Notes

### For AI Agents
This documentation structure is optimized for AI agent navigation:
1. Hierarchical organization by technology category
2. Consistent naming conventions
3. Direct links to specific topics
4. Latest stable versions only

### Quick Commands
```bash
# Search for Flask patterns
grep -r "blueprint" flask/

# Find testing examples
find . -name "*test*" -type f

# List all API references
ls */api/
```

### Updating Documentation
Run `scripts/fetch-all-docs.sh` to update all documentation to latest versions.

## Download Log
EOF

echo "Last updated: $(date '+%Y-%m-%d %H:%M:%S')" >> "$DOCS_ROOT/INDEX.md"
echo "Total size: $(du -sh "$DOCS_ROOT" | cut -f1)" >> "$DOCS_ROOT/INDEX.md"

# =====================================
# CREATE AI AGENT HELPER
# =====================================

cat > "$DOCS_ROOT/AI_AGENT_GUIDE.md" << 'EOF'
# AI Agent Documentation Guide

## Quick Reference Paths

When you need to reference documentation, use these paths:

### Flask Application Development
- Factory pattern: `docs/reference/flask/patterns/index.html`
- Blueprints: `docs/reference/flask/blueprints/index.html`
- Testing: `docs/reference/flask/testing/index.html`
- Configuration: `docs/reference/flask/config/index.html`

### Python 3.13 Features
- Type hints: `docs/reference/python/typing/index.html`
- Async/await: `docs/reference/python/asyncio/index.html`
- Pathlib: `docs/reference/python/pathlib/index.html`

### Frontend Integration
- HTMX attributes: `docs/reference/frontend/htmx-*/index.html`
- Alpine.js directives: `docs/reference/frontend/alpine-*/index.html`
- Tailwind utilities: `docs/reference/frontend/tailwind-*/index.html`

### Testing
- pytest fixtures: `docs/reference/tools/pytest-fixtures/index.html`
- pytest markers: `docs/reference/tools/pytest-markers/index.html`

## Search Patterns

```bash
# Find Flask examples
grep -r "app.route" docs/reference/flask/

# Find testing patterns
grep -r "@pytest" docs/reference/tools/

# Find HTMX examples
grep -r "hx-" docs/reference/frontend/
```

## Version Compliance
Always use patterns from these docs as they represent:
- Python 3.13.6 (latest)
- Flask 3.x (latest stable)
- All other tools in their latest stable versions
EOF

# =====================================
# SUMMARY
# =====================================

log "Documentation fetch complete!"
info "Location: $DOCS_ROOT"
info "Index: $DOCS_ROOT/INDEX.md"
info "AI Guide: $DOCS_ROOT/AI_AGENT_GUIDE.md"
info "Log: $LOG_FILE"

# Show summary
echo ""
echo -e "${GREEN}=== Documentation Summary ===${NC}"
echo "Python docs: $(find "$DOCS_ROOT/python" -name "*.html" 2>/dev/null | wc -l) files"
echo "Flask docs: $(find "$DOCS_ROOT/flask" -name "*.html" 2>/dev/null | wc -l) files"
echo "Frontend docs: $(find "$DOCS_ROOT/frontend" -name "*.html" 2>/dev/null | wc -l) files"
echo "Tools docs: $(find "$DOCS_ROOT/tools" -name "*.html" 2>/dev/null | wc -l) files"
echo "Standards docs: $(find "$DOCS_ROOT/standards" -name "*.html" 2>/dev/null | wc -l) files"
echo "Total size: $(du -sh "$DOCS_ROOT" | cut -f1)"
echo ""
echo -e "${BLUE}View the index at: $DOCS_ROOT/INDEX.md${NC}"