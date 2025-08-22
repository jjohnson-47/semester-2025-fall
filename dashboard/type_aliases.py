"""Type aliases for dashboard application.

This module provides consistent type definitions used throughout the dashboard
to improve code readability and maintainability.
"""

from typing import Any

# Task-related types
type TaskDict = dict[str, Any]
type TaskList = list[TaskDict]
type TaskID = str
type TaskStatus = str  # Literal["blocked", "todo", "doing", "review", "done"]
type TaskPriority = str  # Literal["low", "medium", "high", "critical"]

# Configuration types
type ConfigDict = dict[str, Any]
type CourseDict = dict[str, Any]
type CourseList = list[CourseDict]

# API response types
type APIResponse = dict[str, Any]
type StatsDict = dict[str, int | float]

# Template context types
type TemplateContext = dict[str, Any]

# File path types
type PathLike = str | Any  # Path objects

# Date/time types
type ISODateString = str
