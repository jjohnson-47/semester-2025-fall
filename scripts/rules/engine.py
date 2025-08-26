#!/usr/bin/env python3
"""Course rules engine scaffolding.

Defines a minimal, typed rules engine that can be extended with rule
families (dates, policy, compliance, dependencies). This scaffold is
non-invasive and does not change current build behavior until adopted
by services/build pipeline.
"""

from __future__ import annotations

from typing import Iterable, Protocol

from scripts.rules.models import NormalizedCourse


class Rule(Protocol):
    """A transformation that updates a normalized course snapshot."""

    name: str
    version: str

    def apply(self, context: NormalizedCourse) -> NormalizedCourse:  # pragma: no cover - interface
        ...


class CourseRulesEngine:
    """Composable course rules engine.

    Usage:
    engine = CourseRulesEngine(rules=[DateRules(...), ...])
    normalized = engine.normalize_course("MATH221")
    """

    def __init__(self, rules: Iterable[Rule] | None = None) -> None:
        self._rules: list[Rule] = list(rules or [])

    def add_rule(self, rule: Rule) -> None:
        self._rules.append(rule)

    def normalize_course(self, course_id: str) -> NormalizedCourse:
        # Minimal seed context; actual facts will be populated by service layer
        context = NormalizedCourse(course_id=course_id)
        for rule in self._rules:
            context = rule.apply(context)
            context.add_provenance(rule.name, rule.version)
        return context

