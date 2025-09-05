#!/usr/bin/env python3
"""Dashboard startup coordinator and health checks.

Provides a minimal readiness gate separate from liveness.
This is the only module where contextlib.suppress usage is permitted
by CI policy, for best-effort initialization during startup.
"""

from __future__ import annotations

from contextlib import suppress

from dashboard.db import Database

_startup_ok: bool = False
_error: str | None = None


def startup_init(db: Database) -> None:
    """Perform best-effort initialization for readiness.

    - Ensures the SQLite schema exists
    - Performs a lightweight health query
    """
    global _startup_ok, _error
    with suppress(Exception):
        db.initialize()
    try:
        health = db.health()
        _startup_ok = bool(health.get("ok", True))
        _error = None if _startup_ok else str(health.get("error"))
    except Exception as exc:  # pragma: no cover - unexpected
        _startup_ok = False
        _error = str(exc)


def is_live() -> bool:
    """Liveness: process is up."""
    return True


def is_ready() -> bool:
    """Readiness: core dependencies initialized."""
    return _startup_ok


def last_error() -> str | None:
    return _error
