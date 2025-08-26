#!/usr/bin/env python3
"""Basic import tests for new scaffolds to ensure they are wired correctly."""

from __future__ import annotations

from scripts.build_pipeline import BuildPipeline
from scripts.rules.dates import DateRules
from scripts.rules.engine import CourseRulesEngine
from scripts.rules.models import NormalizedCourse, NormalizedField
from scripts.services.changes import Change, ChangeDetector
from scripts.services.course_service import CourseService
from scripts.services.validation import ValidationGateway, ValidationResult
from scripts.utils.semester_calendar import SemesterCalendar


def test_rules_engine_minimal() -> None:
    engine = CourseRulesEngine()
    nc = engine.normalize_course("MATH221")
    assert isinstance(nc, NormalizedCourse)


def test_date_rules_instantiation() -> None:
    dr = DateRules(calendar=SemesterCalendar())
    cs = NormalizedCourse(course_id="MATH221")
    out = dr.apply(cs)
    assert out is cs


def test_course_service_scaffold() -> None:
    svc = CourseService("MATH221")
    ctx = svc.get_template_context("syllabus")
    assert ctx["course"]["code"] == "MATH221"


def test_build_pipeline_runs() -> None:
    bp = BuildPipeline(["MATH221"])  # no-op stages
    bp.run(force=True)
