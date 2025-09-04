"""Utilities for v1.1.0 schema helpers.

Provides stable ID generation expected by tests.
"""

from __future__ import annotations

import hashlib


def create_stable_id(course_code: str, term: str, year: int) -> str:
    """Create a deterministic stable ID string.

    Format: "{course}-{term}-{year}-{hash8}", all lowercase.
    Hash is SHA1 of "{course}:{term}:{year}" to ensure stability.
    """
    cc = str(course_code).lower()
    tt = str(term).lower()
    yy = int(year)
    basis = f"{cc}:{tt}:{yy}".encode()
    h = hashlib.sha1(basis).hexdigest()[:8]
    return f"{cc}-{tt}-{yy}-{h}"
