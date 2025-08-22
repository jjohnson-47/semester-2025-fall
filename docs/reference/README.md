# Documentation Reference Library

## Overview
This directory contains comprehensive documentation for all project technologies, organized for optimal AI agent accessibility and developer reference.

## Structure

```
docs/reference/
├── python/          # Python 3.13.6 documentation
├── flask/           # Flask 3.x and ecosystem
├── frontend/        # HTMX, Alpine.js, Tailwind CSS
├── tools/           # pytest, UV, Ruff, Black, etc.
├── standards/       # Web standards, accessibility
├── flask-reference/ # Flask quick reference (minimal)
├── INDEX.md         # Master documentation index
└── AI_AGENT_GUIDE.md # AI navigation guide
```

## Quick Start

### Download Documentation
```bash
# Download all documentation (comprehensive)
make docs

# Download Flask documentation only (quick)
make docs-flask
```

### Access Documentation
- **Master Index**: [INDEX.md](INDEX.md)
- **AI Agent Guide**: [AI_AGENT_GUIDE.md](AI_AGENT_GUIDE.md)
- **Flask Quick Ref**: [flask-reference/LOCAL_INDEX.html](flask-reference/LOCAL_INDEX.html)

## Version Matrix

| Technology | Version | Documentation Path |
|------------|---------|-------------------|
| Python | 3.13.6 | `python/` |
| Flask | 3.x (latest) | `flask/core/` |
| Jinja2 | 3.x | `flask/jinja2/` |
| pytest | 8.x | `tools/pytest/` |
| UV | Latest | `tools/uv/` |
| HTMX | 2.x | `frontend/htmx/` |
| Alpine.js | 3.x | `frontend/alpine-*/` |
| Tailwind CSS | 3.x | `frontend/tailwind-*/` |

## For AI Agents

### Navigation Patterns
```python
# Flask application patterns
docs/reference/flask/patterns/index.html
docs/reference/flask/blueprints/index.html

# Python 3.13 features
docs/reference/python/typing/index.html
docs/reference/python/asyncio/index.html

# Testing documentation
docs/reference/tools/pytest/index.html
docs/reference/flask/testing/index.html
```

### Search Commands
```bash
# Find Flask examples
grep -r "create_app" flask/

# Find testing patterns
grep -r "fixture" tools/pytest/

# Find HTMX attributes
ls frontend/htmx-*/
```

## Documentation Sources

All documentation is fetched from official sources:
- Python: docs.python.org/3.13/
- Flask: flask.palletsprojects.com/en/stable/
- Jinja2: jinja.palletsprojects.com/en/stable/
- pytest: docs.pytest.org/en/stable/
- HTMX: htmx.org/
- Alpine.js: alpinejs.dev/
- Tailwind: tailwindcss.com/docs/

## Updating Documentation

To ensure you have the latest documentation:

```bash
# Update all documentation
make docs

# Check last update
cat docs/reference/INDEX.md | grep "Last updated"
```

## Best Practices

1. **Always use latest patterns**: Documentation reflects current stable versions
2. **Reference before implementing**: Check docs for proper patterns
3. **Version awareness**: Python 3.13.6, Flask 3.x, all others latest stable
4. **Offline capability**: All docs are available offline after download

## Integration with Project

This documentation supports:
- Flask dashboard development
- Course management system
- Testing and quality assurance
- Frontend interactivity
- API development
- Deployment preparation

## Notes

- Documentation is in `.gitignore` to avoid repository bloat
- Run `make docs` after cloning to get local reference
- Total size: ~100-200MB depending on resources downloaded
- Organized for both human and AI agent navigation
