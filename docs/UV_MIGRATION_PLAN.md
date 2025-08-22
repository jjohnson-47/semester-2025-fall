# UV Migration Plan for Semester Management System

## Executive Summary

Migrate from traditional pip/venv to uv for Python package and environment management. UV is a Rust-based, ultra-fast Python package manager that replaces pip, pip-tools, pipx, poetry, pyenv, and virtualenv with a single tool.

## Key Benefits for This Project

### 1. **Speed Improvements**

- **10-100x faster** than pip for package installation
- Near-instant environment creation
- Faster CI/CD builds in GitHub Actions

### 2. **Simplified Workflow**

- Single tool replaces multiple Python tools
- Built-in lockfile support (no more pip-freeze)
- Automatic Python version management

### 3. **Project-Centric Features**

- `pyproject.toml` as single source of truth
- Dependency groups (dev, docs, dashboard, etc.)
- Workspace support for multi-project repos

### 4. **GitHub Integration**

- Native GitHub Actions support
- Faster dependency caching
- Reproducible builds across platforms

## Migration Architecture

### Current Setup

```
semester-2025-fall/
├── requirements.txt         # Basic dependencies
├── dashboard/requirements.txt # Dashboard deps
├── venv/                    # Virtual environment
└── Makefile                 # Build orchestration
```

### Target UV Setup

```
semester-2025-fall/
├── pyproject.toml          # All project config
├── uv.lock                 # Locked dependencies
├── .python-version         # Python version pin
└── Makefile               # Simplified commands
```

## Implementation Plan

### Phase 1: UV Installation & Setup

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or on macOS/Linux with homebrew
brew install uv

# Initialize project
uv init --name semester-2025-fall --python 3.11
```

### Phase 2: Create pyproject.toml

```toml
[project]
name = "semester-2025-fall"
version = "1.0.0"
description = "Course management for KPC Fall 2025"
requires-python = ">=3.11"
dependencies = [
    "jinja2>=3.1.2",
    "pyyaml>=6.0",
    "jsonschema>=4.17.3",
    "python-dateutil>=2.8.2",
    "pytz>=2023.3",
    "markdown>=3.4.3",
]

[project.optional-dependencies]
dashboard = [
    "flask>=2.0",
    "watchdog>=3.0",
]
dev = [
    "pytest>=7.3.1",
    "black>=23.3.0",
    "ruff>=0.1.0",
]
docs = [
    "weasyprint>=59.0",  # For PDF generation
    "pypandoc>=1.11",
]

[tool.uv]
dev-dependencies = [
    "ipython>=8.0.0",  # Interactive development
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### Phase 3: Makefile Updates

```makefile
# UV-based commands
UV := uv

# Initialize environment (replaces venv creation)
init:
 @$(UV) sync
 @echo "✓ Environment ready"

# Run with proper environment
syllabi:
 @$(UV) run python scripts/build_syllabi.py

# Dashboard with optional deps
dash:
 @$(UV) sync --extra dashboard
 @$(UV) run python dashboard/app.py

# Development tools
format:
 @$(UV) run black scripts/ dashboard/

lint:
 @$(UV) run ruff check scripts/ dashboard/

# Add new dependency
add-dep:
 @$(UV) add $(PACKAGE)
```

### Phase 4: Scripts & Tools Integration

#### Script Execution

```bash
# Old way
source venv/bin/activate && python scripts/build_syllabi.py

# UV way (automatic environment)
uv run python scripts/build_syllabi.py
```

#### Inline Script Dependencies

```python
#!/usr/bin/env python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests",
#   "rich",
# ]
# ///

import requests
from rich import console
# Script runs with its own dependencies!
```

### Phase 5: GitHub Actions Integration

```yaml
name: Build Course Materials

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v3
        with:
          enable-cache: true

      - name: Install Python
        run: uv python install 3.11

      - name: Install dependencies
        run: uv sync

      - name: Run tests
        run: uv run pytest

      - name: Build materials
        run: |
          uv run make syllabi
          uv run make schedules
```

## Useful UV Features for This Project

### 1. **Dependency Groups**

Separate dependencies by purpose:

- `core`: Essential for syllabus generation
- `dashboard`: Flask and web dependencies
- `dev`: Testing and linting tools
- `docs`: PDF generation tools

### 2. **Platform-Specific Locks**

```bash
# Generate cross-platform lockfile
uv lock --universal

# Platform-specific resolution
uv sync --platform windows
```

### 3. **Tool Management**

```bash
# Install and run tools without polluting project
uv tool install ruff
uv tool run ruff check .

# Run one-off commands
uv run --with pandas python -c "import pandas; print(pandas.__version__)"
```

### 4. **Python Version Management**

```bash
# Install specific Python version
uv python install 3.11

# Pin project to Python version
uv python pin 3.11

# List available versions
uv python list
```

### 5. **Workspace Support** (Future)

If you expand to multiple semesters:

```toml
[tool.uv.workspace]
members = [
    "fall-2025",
    "spring-2026",
    "shared-tools",
]
```

## Migration Benefits Summary

| Aspect | Current (pip/venv) | With UV |
|--------|-------------------|---------|
| Install time | ~30-60 seconds | ~2-5 seconds |
| Lock generation | Manual pip freeze | Automatic |
| Python versions | System dependent | Managed by UV |
| CI/CD speed | 2-3 minutes | 20-30 seconds |
| Dependency groups | Multiple requirements.txt | Single pyproject.toml |
| Tool isolation | Separate venvs | `uv tool` command |
| Cross-platform | Platform-specific locks | Universal lockfile |

## Risk Mitigation

1. **Backwards Compatibility**: Keep requirements.txt during transition
2. **Team Training**: UV commands are similar to pip
3. **Rollback Plan**: Git history preserves old setup
4. **Testing**: Parallel testing before full migration

## Implementation Timeline

- **Week 1**: Install UV, create pyproject.toml
- **Week 2**: Update Makefile, test builds
- **Week 3**: Migrate GitHub Actions
- **Week 4**: Remove old venv/requirements.txt

## Next Steps

1. Install UV locally
2. Run `uv init` in project
3. Create pyproject.toml with dependencies
4. Test core functionality
5. Update documentation
6. Migrate CI/CD
