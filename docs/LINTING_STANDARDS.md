# Code Quality and Linting Standards

## Overview

This document defines the code quality standards and linting practices for the KPC Fall 2025 Semester Management System. These standards ensure consistent, maintainable, and high-quality code across the entire codebase.

## Tools and Configuration

### Primary Tools

1. **Ruff** (v0.8.6+) - Fast Python linter and formatter
   - Configuration: `pyproject.toml`
   - Combines functionality of multiple tools (flake8, isort, etc.)
   - Auto-fixes available for most issues

2. **MyPy** (v1.14.1+) - Static type checker
   - Configuration: `pyproject.toml`
   - Type hints required for all public functions
   - Gradual typing approach for existing code

3. **Pre-commit** - Git hook framework
   - Configuration: `.pre-commit-config.yaml`
   - Runs automatically on git commit
   - Ensures code quality before commits

## Linting Rules

### Critical Issues (Must Fix)

- **F821**: Undefined names - All variables must be defined before use
- **E722**: Bare except clauses - Always specify exception types
- **E402**: Module imports not at top - Keep imports organized at file start

### Code Quality Issues

- **E741**: Ambiguous variable names - Avoid single letters like `l`, `O`, `I`
- **SIM102**: Collapsible if statements - Combine nested conditions with `and`
- **B007**: Unused loop variables - Mark with underscore (`_`)
- **ARG001/002**: Unused function arguments - Remove or document why needed
- **F841**: Unused variables - Remove or use underscore prefix

### Style Guidelines

- **Line Length**: Maximum 100 characters (configurable)
- **Indentation**: 4 spaces for Python code
- **Import Order**: Standard library → Third-party → Local (automated by Ruff)
- **String Quotes**: Double quotes preferred, single quotes acceptable

## Type Hints

### Required Type Hints

```python
# Function signatures
def process_course(course_id: str) -> dict[str, Any]:
    ...

# Class attributes
class CourseService:
    courses: dict[str, Course]
    cache: dict[str, Any]
    
# Complex types
from typing import Optional, Union, Literal

CourseType = Literal["MATH", "STAT", "CS"]
```

### Type Hint Exemptions

- Test fixtures and test helper functions
- Private methods with obvious types
- Lambda functions and comprehensions

## Pre-commit Workflow

### Installation

```bash
# Install pre-commit
uv pip install pre-commit

# Install git hooks
pre-commit install

# Run on all files (initial setup)
pre-commit run --all-files
```

### Manual Checks

```bash
# Run linting
uv run ruff check .

# Run formatting
uv run ruff format .

# Run type checking
uv run mypy scripts/ dashboard/

# Run all pre-commit hooks
pre-commit run --all-files
```

## CI/CD Integration

### GitHub Actions

The CI pipeline enforces all linting standards:

1. **Lint Check**: Runs on every push/PR
2. **Type Check**: Validates type hints
3. **Format Check**: Ensures consistent formatting
4. **JSON Validation**: Checks course data schemas

### Failure Handling

If CI fails due to linting:

1. Run `uv run ruff check . --fix` locally
2. Run `uv run ruff format .`
3. Fix any remaining issues manually
4. Commit and push fixes

## Common Patterns and Solutions

### Unused Arguments in Tests

```python
# Use underscore prefix for required but unused fixtures
def test_something(self, _course_service, _validation_gateway):
    ...
```

### Handling Import Cycles

```python
# Use TYPE_CHECKING for type-only imports
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dashboard.services import CourseService
```

### Unicode Characters

```python
# Use escape sequences instead of literal unicode
multiplication_sign = '\u00d7'  # Not '×'
```

## Exemptions and Overrides

### File-level Exemptions

```python
# ruff: noqa: F401  # Unused imports in __init__.py
```

### Line-level Exemptions

```python
result = complex_calculation()  # noqa: E501 (line too long)
```

### Project-wide Exemptions

Configured in `pyproject.toml`:

```toml
[tool.ruff]
ignore = [
    "E501",  # Line too long (use formatter instead)
    "D100",  # Missing module docstring (optional)
]
```

## Best Practices

1. **Fix Issues Immediately**: Don't accumulate technical debt
2. **Use Auto-fix**: Let tools fix what they can automatically
3. **Document Exemptions**: Explain why rules are disabled
4. **Regular Updates**: Keep tools updated to latest versions
5. **Team Consistency**: All developers use same tool versions

## Gradual Adoption

For existing code:

1. **Phase 1**: Fix critical errors (F821, E722)
2. **Phase 2**: Add type hints to public APIs
3. **Phase 3**: Fix style issues (formatting, naming)
4. **Phase 4**: Comprehensive type coverage

## Resources

- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [MyPy Documentation](https://mypy.readthedocs.io/)
- [Pre-commit Documentation](https://pre-commit.com/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)

## Maintenance

This document should be updated when:

- Tool versions change significantly
- New linting rules are adopted
- Team agrees on new standards
- CI/CD pipeline is modified

Last Updated: December 2025
Tool Versions: Ruff 0.8.6, MyPy 1.14.1, Pre-commit 4.0.1