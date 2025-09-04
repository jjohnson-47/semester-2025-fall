# MyPy Type Checking Strategy

## Executive Summary

The project has ~112 MyPy errors across 20 files. These are primarily missing type annotations rather than actual type safety issues. This document outlines a strategic approach to systematically address these while building intelligent type safety into the project.

## Current State Analysis

### Error Categories

1. **Missing Type Annotations (60%)**
   - Function return types not specified
   - Function parameters missing types
   - Class methods without annotations

2. **Type Inference Issues (20%)**
   - Variables needing explicit type hints
   - Return values where MyPy can't infer the type

3. **Structural Issues (15%)**
   - `@staticmethod` misuse in app.py
   - Import type stubs missing (pytz, yaml, markdown)

4. **Logic Issues (5%)**
   - Actual type mismatches that need fixing
   - Incompatible return types

## High-Level Strategy

### Phase 1: Foundation (Immediate)

**Goal:** Fix critical type errors that affect runtime behavior

1. **Install Missing Type Stubs**

   ```bash
   uv add --dev types-pytz types-PyYAML types-Markdown
   ```

2. **Fix Actual Type Errors**
   - `dashboard/models.py:338` - Float/int assignment
   - `scripts/utils/sync_course_guides.py:70` - Bool return type
   - `scripts/generate_dashboard_config.py` - Collection type issues

3. **Create Type Alias Module**

   ```python
   # dashboard/types.py
   from typing import TypeAlias, Any

   TaskDict: TypeAlias = dict[str, Any]
   TaskList: TypeAlias = list[TaskDict]
   ConfigDict: TypeAlias = dict[str, Any]
   ```

### Phase 2: Core Components (Week 1)

**Goal:** Type-safe core functionality

1. **Models Layer** (`dashboard/models.py`)
   - Add comprehensive type hints to Task and TaskGraph classes
   - Use TypedDict for structured data
   - Create proper return type annotations

2. **Service Layer** (`dashboard/services/`)
   - Type all service methods
   - Use Protocol classes for interfaces
   - Add return type guarantees

3. **Configuration** (`dashboard/config.py`)
   - Type all config methods
   - Use Literal types for constants
   - Add overload signatures where needed

### Phase 3: API Layer (Week 2)

**Goal:** Type-safe API endpoints

1. **Route Handlers** (`dashboard/api/`)
   - Add Flask-specific type hints
   - Use Response type annotations
   - Type request/response data structures

2. **Decorators** (`dashboard/utils/decorators.py`)
   - Use ParamSpec and TypeVar for generic decorators
   - Add proper Callable signatures
   - Type decorator factories

### Phase 4: Scripts & Tools (Week 3)

**Goal:** Type-safe build scripts

1. **Build Scripts** (`scripts/`)
   - Add return types to all functions
   - Type command-line argument handling
   - Use Path type consistently

2. **Dashboard Tools** (`dashboard/tools/`)
   - Type task generation functions
   - Add validation type hints
   - Use TypedDict for structured outputs

## Implementation Patterns

### Pattern 1: Gradual Typing

```python
# Start with Any, refine later
def process_data(data: Any) -> dict[str, Any]:
    # Implementation
    return result  # Type: dict[str, Any]

# Refine to specific types
def process_data(data: TaskDict) -> ProcessedResult:
    # Implementation
    return ProcessedResult(...)
```

### Pattern 2: Type Guards

```python
from typing import TypeGuard

def is_valid_task(data: Any) -> TypeGuard[TaskDict]:
    return (
        isinstance(data, dict) and
        "id" in data and
        "title" in data
    )
```

### Pattern 3: Protocol Classes

Note: In v2, the legacy `TaskService` has been removed. Prefer repository-style
protocols that reflect DB operations.

```python
from typing import Protocol

class Repository(Protocol):
    def get_task(self, task_id: str) -> TaskDict | None: ...
    def list_tasks(self) -> list[TaskDict]: ...
    def update_task_fields(self, task_id: str, fields: dict[str, object]) -> bool: ...
```

## Automation & Tooling

### Pre-commit Integration

```yaml
# Add to .pre-commit-config.yaml
- repo: local
  hooks:
    - id: mypy-incremental
      name: MyPy incremental checking
      entry: uv run mypy --incremental
      language: system
      types: [python]
```

### Auto-fix Script

```python
# scripts/fix_types.py
#!/usr/bin/env python3
"""Auto-add basic type hints using MonkeyType or similar."""

def add_return_none_hints():
    """Add -> None to functions without return types."""
    ...

def add_parameter_hints():
    """Infer parameter types from usage."""
    ...
```

### CI Configuration

```yaml
# .github/workflows/ci.yml
- name: Type Check
  run: |
    uv run mypy . --ignore-missing-imports
    # Allow failure initially, enforce later
  continue-on-error: true
```

## Success Metrics

1. **Week 1:** Reduce errors to < 80 (30% reduction)
2. **Week 2:** Reduce errors to < 40 (65% reduction)
3. **Week 3:** Reduce errors to < 10 (90% reduction)
4. **Week 4:** Full type coverage with strict mode

## Benefits

1. **Immediate**
   - Catch type-related bugs before runtime
   - Better IDE autocomplete and hints
   - Self-documenting code

2. **Long-term**
   - Easier refactoring with confidence
   - Reduced debugging time
   - Better code maintainability
   - Improved onboarding for new developers

## Next Steps

1. Install missing type stubs (5 min)
2. Fix critical type errors (30 min)
3. Create type alias module (15 min)
4. Begin Phase 2 with models.py (1-2 hours)

## Notes

- Use `# type: ignore[specific-error]` sparingly for unfixable issues
- Prefer `Any` over no annotation initially
- Focus on public APIs first, internals later
- Document complex type decisions in comments
