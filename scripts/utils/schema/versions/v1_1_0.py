"""Compatibility module mirroring the v1.1.0 helpers package.

Re-exports helpers from `scripts.utils.schema.versions.v1_1_0` package for
code that imported as a module instead of the package path.
"""

from __future__ import annotations

from scripts.utils.schema.versions.v1_1_0 import create_stable_id  # noqa: F401

