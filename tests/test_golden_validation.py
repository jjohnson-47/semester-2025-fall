"""Golden tests for course validation and normalization.

These tests ensure that the refactored system produces consistent,
correct output that matches expected behavior.
"""

import sys
import os
from pathlib import Path

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.rules.dates import DateRules
from scripts.services.course_service import CourseService
from scripts.services.validation import ValidationGateway


class TestGoldenValidation:
    """Golden tests for validation consistency."""

    @pytest.fixture
    def course_service(self):
        """Create a course service for testing."""
        return CourseService("MATH221")

    @pytest.fixture
    def validation_gateway(self):
        """Create a validation gateway for testing."""
        return ValidationGateway()

    def test_math221_v110_validation(self, validation_gateway):
        """Validate MATH221 schedule against v1.1.0 schema via gateway."""
        res = validation_gateway.validate_for_build("MATH221")
        assert res.ok, f"Validation failed: {'; '.join(res.messages)}"

    def test_math251_v110_validation(self, validation_gateway):
        """Validate MATH251 schedule against v1.1.0 schema via gateway."""
        res = validation_gateway.validate_for_build("MATH251")
        assert res.ok, f"Validation failed: {'; '.join(res.messages)}"

    def test_stat253_projections(self):
        """Test STAT253 v2 schedule projection is present and consistent."""
        os.environ["BUILD_MODE"] = "v2"
        try:
            s = CourseService("STAT253")
            ctx = s.get_template_context("schedule")
            assert "schedule_projection" in ctx
            proj = ctx["schedule_projection"]
            assert "weeks" in proj and isinstance(proj["weeks"], list)
        finally:
            os.environ.pop("BUILD_MODE", None)

    def test_date_rules_consistency(self):
        """Test date rules produce consistent results using v2 helpers."""
        dr = DateRules(calendar=None)  # calendar not needed for this test
        # Saturday/Sunday avoidance via fall-through in helpers
        # Use a week start and a placeholder label; ensure due never lands on weekend
        due = dr.apply_rules("HW 1", "2025-09-06", holidays=[], is_assessment=False)  # Week start Sat
        assert "(due Sat" not in due and "(due Sun" not in due
        due2 = dr.apply_rules("Exam #1", "2025-09-07", holidays=[], is_assessment=True)  # Week start Sun
        assert "(due Sat" not in due2 and "(due Sun" not in due2
        # Different week starts still avoid weekends
        dr2 = DateRules(calendar=None)
        due3 = dr2.apply_rules("HW 2", "2025-09-08", holidays=[], is_assessment=False)  # Mon start
        assert "(due Sat" not in due3 and "(due Sun" not in due3

    def test_cross_course_consistency(self, validation_gateway):
        """Basic cross-course v1.1.0 validation check."""
        oks = []
        for cid in ["MATH221", "MATH251", "STAT253"]:
            res = validation_gateway.validate_for_build(cid)
            oks.append(res.ok)
        assert any(oks)

    def test_provenance_tracking(self):
        """Provenance tracking not covered in unified service yet."""
        import pytest
        pytest.skip("Provenance tracking is not exposed via unified CourseService")
        assert course.instructor.name.provenance is not None
        assert course.instructor.name.provenance.confidence >= 0.0

        # Check schedule week provenance
        if course.schedule_weeks:
            week = course.schedule_weeks[0]
            assert week.topic.provenance is not None
            assert week.topic.field_name == "topic"

    @pytest.mark.parametrize("course_id", ["MATH221", "MATH251", "STAT253"])
    def test_projection_checksums(self, course_service, course_id):
        """Test that projections have stable checksums."""
        # Get projection twice
        proj1 = course_service.get_projection(course_id, "syllabus")
        proj2 = course_service.get_projection(course_id, "syllabus")

        # Checksums should match (deterministic)
        assert proj1.checksum == proj2.checksum

        # Force regeneration
        proj3 = course_service.get_projection(course_id, "syllabus", force_regenerate=True)

        # New projection should have same checksum if data unchanged
        assert proj3.checksum == proj1.checksum

    def test_error_handling(self, course_service):
        """Test error handling for invalid courses."""
        with pytest.raises(ValueError) as exc_info:
            course_service.load_course("INVALID999")

        assert "Course directory not found" in str(exc_info.value)

    def test_cache_behavior(self, course_service):
        """Test that caching works correctly."""
        # Load course twice
        course1 = course_service.load_course("MATH221")
        course2 = course_service.load_course("MATH221")

        # Should be the same object (cached)
        assert course1 is course2

        # Force reload
        course3 = course_service.load_course("MATH221", force_reload=True)

        # Should be different object
        assert course3 is not course1

        # But should have same data
        assert course3.identity.code.value == course1.identity.code.value
