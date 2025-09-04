"""Database package for the dashboard.

Provides a thin repository layer around SQLite to support:
- Tasks, dependencies, events, scores, and now_queue tables
- Import/export to JSON for backups and portability

This package is intentionally lightweight and pure-Python to avoid
runtime dependency surprises. The ORMs are overkill for this use case.
"""

from __future__ import annotations

__all__ = [
    "Database",
    "DatabaseConfig",
]

from .repo import Database, DatabaseConfig  # re-export for convenience
