# UV Technical Implementation Plan

## Objective Analysis

### What UV Actually Does

- **Package resolver**: Faster dependency resolution using Rust
- **Environment manager**: Replaces virtualenv with built-in environment handling
- **Lockfile generator**: Creates reproducible dependency sets
- **Python installer**: Downloads and manages Python interpreters

### Relevant Features for This Project

#### 1. Single-File Dependency Management

**Current Problem**: Multiple requirements.txt files (root + dashboard)
**UV Solution**: All dependencies in pyproject.toml with optional groups

```toml
[project]
dependencies = ["jinja2", "pyyaml", "jsonschema", "python-dateutil", "pytz", "markdown"]

[project.optional-dependencies]
dashboard = ["flask", "watchdog"]
```

**Benefit**: Eliminates dependency duplication and sync issues

#### 2. Lockfile for Reproducibility

**Current Problem**: No lockfile, `pip freeze` captures system-wide packages
**UV Solution**: `uv.lock` automatically maintained

```bash
# Generates uv.lock with exact versions
uv lock

# Anyone can reproduce exact environment
uv sync
```

**Benefit**: Guarantees same versions across development machines and CI

#### 3. Script Dependencies

**Current Problem**: Scripts fail if dependencies missing
**UV Solution**: Scripts declare their own dependencies

```python
# scripts/build_syllabi.py
# /// script
# dependencies = ["jinja2", "pyyaml", "markdown"]
# ///
```

**Benefit**: Scripts are self-contained, can run anywhere with uv

## Implementation Steps

### Step 1: Install UV

```bash
# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add to PATH
echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
```

### Step 2: Convert Project Structure

#### Create pyproject.toml

```toml
[project]
name = "semester-2025-fall"
version = "0.1.0"
requires-python = ">=3.9"  # Match current Python
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
    "Flask>=2.0",
    "watchdog>=3.0",
]

[tool.uv]
package = false  # This is not a distributable package
```

### Step 3: Update Makefile

Replace virtualenv commands with uv:

```makefile
# Old
init:
 python3 -m venv venv
 . venv/bin/activate && pip install -r requirements.txt

# New
init:
 uv sync
 uv sync --extra dashboard

# Old command execution
syllabi:
 . $(VENV)/bin/activate && $(PYTHON) scripts/build_syllabi.py

# New command execution
syllabi:
 uv run python scripts/build_syllabi.py
```

### Step 4: Fix Import Issues

Current scripts use manual .env loading. With uv, use proper environment:

```python
# Remove manual .env loading
# env_file = Path(__file__).parent.parent / '.env'
# if env_file.exists():
#     with open(env_file) as f:
#         for line in f:
#             ...

# Use python-dotenv properly
from dotenv import load_dotenv
load_dotenv()
```

### Step 5: GitHub Actions

```yaml
name: CI
on: [push]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv sync
      - run: uv run python scripts/validate_json.py
      - run: uv run python scripts/build_syllabi.py --ci
```

## What We're NOT Using

### Features Not Relevant

- **Publishing**: We're not making a PyPI package
- **Workspace**: Single project, not monorepo
- **Python compilation**: Using system Python is fine
- **Global tools**: Project-specific tools only

### Overkill Features

- **Universal locks**: Single platform (Linux) for deployment
- **Build backend**: Not building distributions
- **Complex versioning**: Simple project versioning

## Measurable Improvements

| Metric | Current | With UV |
|--------|---------|---------|
| Dependency install | ~15s (fresh) | ~2s |
| Environment creation | ~5s | <1s |
| CI setup time | ~45s | ~10s |
| Lockfile | None | Automatic |
| Python version | System-dependent | Pinned |

## Minimal Migration Path

### Day 1: Local Development

1. Install uv
2. Create pyproject.toml from requirements.txt
3. Run `uv sync`
4. Test: `uv run python scripts/validate_json.py`

### Day 2: Update Scripts

1. Update Makefile commands
2. Remove venv references
3. Test all make targets

### Day 3: CI/CD

1. Update GitHub Actions
2. Remove pip commands
3. Verify builds pass

### Day 4: Cleanup

1. Delete requirements.txt files
2. Delete venv directory
3. Update documentation

## Command Mapping

| Task | Old Command | UV Command |
|------|------------|------------|
| Install deps | `pip install -r requirements.txt` | `uv sync` |
| Add package | `pip install X && pip freeze > requirements.txt` | `uv add X` |
| Run script | `source venv/bin/activate && python script.py` | `uv run python script.py` |
| Update deps | `pip install --upgrade` | `uv lock --upgrade` |
| Show deps | `pip list` | `uv pip list` |

## Expected Issues & Solutions

### Issue 1: Missing system packages

UV doesn't install system packages needed for weasyprint
**Solution**: Document system deps, use Docker for CI

### Issue 2: Dashboard Flask app

Flask dev server needs special handling
**Solution**: Create run script or use `uv run flask`

### Issue 3: IDE Integration

VSCode might not recognize uv environment
**Solution**: Point VSCode to `.venv` created by uv

## Success Criteria

✅ All scripts run with `uv run`
✅ Single pyproject.toml replaces all requirements.txt
✅ CI/CD uses uv successfully
✅ Lockfile ensures reproducible builds
✅ No virtualenv activation needed
