#!/usr/bin/env python3
"""Validation gateway (scaffold).

Coalesces schema and business-rule validation prior to builds and
intelligence projections. Real implementations will compose existing
validators and new rule-based checks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class ValidationResult:
    ok: bool
    messages: List[str] = field(default_factory=list)

    @staticmethod
    def merge(results: List["ValidationResult"]) -> "ValidationResult":
        ok = all(r.ok for r in results)
        msgs = [m for r in results for m in r.messages]
        return ValidationResult(ok=ok, messages=msgs)


class ValidationGateway:
    """Aggregate validation entry point (placeholder)."""

    def validate_for_build(self, course_id: str) -> ValidationResult:
        _ = course_id
        return ValidationResult(ok=True, messages=["not implemented: schema/business composition"])

    def validate_for_intelligence(self, course_id: str) -> ValidationResult:
        _ = course_id
        return ValidationResult(ok=True, messages=["not implemented: intelligence preconditions"])

