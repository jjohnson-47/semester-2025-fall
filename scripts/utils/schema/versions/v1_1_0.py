"""Compatibility module mirroring the v1.1.0 helpers package.

Re-exports helpers from `scripts.utils.schema.versions.v1_1_0` package for
code that imported as a module instead of the package path.
"""

from __future__ import annotations

import warnings

from scripts.utils.schema.versions.v1_1_0 import create_stable_id  # noqa: F401

warnings.warn(
    "scripts.utils.schema.versions.v1_1_0 (module file) is deprecated; "
    "prefer importing from the package scripts.utils.schema.versions.v1_1_0. "
    "This shim will be removed after Fall 2025.",
    DeprecationWarning,
    stacklevel=2,
)
