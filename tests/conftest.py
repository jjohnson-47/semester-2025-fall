"""Pytest configuration for test discovery and import path.

Ensures the repository root is on sys.path so tests can import
project modules like `scripts.validate_json` reliably across environments.
"""

from __future__ import annotations

import sys
from pathlib import Path


def _ensure_repo_root_on_path() -> None:
    """Prepend the repository root to sys.path if missing.

    This makes `import scripts...` work regardless of how pytest computes
    its rootdir when invoked (e.g., `pytest`, `pytest tests/`).
    """

    repo_root = Path(__file__).resolve().parents[1]
    repo_root_str = str(repo_root)
    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)


_ensure_repo_root_on_path()
