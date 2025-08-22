"""Type aliases for dashboard application.

This module provides consistent type definitions used throughout the dashboard
to improve code readability and maintainability.
"""

from typing import Any, TypeAlias

# Task-related types
TaskDict: TypeAlias = dict[str, Any]
TaskList: TypeAlias = list[TaskDict]
TaskID: TypeAlias = str
TaskStatus: TypeAlias = str  # Literal["blocked", "todo", "doing", "review", "done"]
TaskPriority: TypeAlias = str  # Literal["low", "medium", "high", "critical"]

# Configuration types
ConfigDict: TypeAlias = dict[str, Any]
CourseDict: TypeAlias = dict[str, Any]
CourseList: TypeAlias = list[CourseDict]

# API response types
APIResponse: TypeAlias = dict[str, Any]
StatsDict: TypeAlias = dict[str, int | float]

# Template context types
TemplateContext: TypeAlias = dict[str, Any]

# File path types
PathLike: TypeAlias = str | Any  # Path objects

# Date/time types
ISODateString: TypeAlias = str