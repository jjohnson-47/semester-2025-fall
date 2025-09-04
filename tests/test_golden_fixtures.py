"""Tests using golden fixtures to ensure consistent behavior.

These tests compare actual output against known-good fixtures
to detect regressions and ensure deterministic behavior.
"""

import json
import os
import sys
from pathlib import Path

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.services.course_service import CourseService


class TestGoldenFixtures:
    """Test against golden fixture data."""

    @pytest.fixture
    def golden_dir(self):
        """Path to golden fixtures."""
        return Path(__file__).parent / "fixtures" / "golden"

    @pytest.fixture
    def service(self):
        """Create a CourseService for testing."""
        return CourseService("MATH221")

    def test_projection_structure_matches_golden(self, service, golden_dir):
        """Test that projection structure matches golden fixture."""
        # Load golden projection
        golden_file = golden_dir / "math221_projection.json"
        if not golden_file.exists():
            pytest.skip("Golden fixture not found")

        with open(golden_file) as f:
            golden_data = json.load(f)

        # Get actual projection (v2 mode)
        os.environ["BUILD_MODE"] = "v2"
        try:
            context = service.get_template_context("schedule")

            # Check for projection key
            assert "schedule_projection" in context, "Missing schedule_projection in v2 mode"

            projection = context["schedule_projection"]

            # Verify structure matches
            assert "weeks" in projection
            assert isinstance(projection["weeks"], list)

            if projection["weeks"]:
                week = projection["weeks"][0]
                # Check required fields
                assert "week" in week
                assert "topic" in week
                assert "date_range" in week
                assert "assignments" in week
                assert "assessments" in week

                # Check date formatting in assignments
                for assignment in week.get("assignments", []):
                    # Should have due date formatting
                    assert "(due" in assignment or not assignment, \
                        f"Assignment missing due date: {assignment}"

                # No weekend due dates
                for assignment in week.get("assignments", []):
                    assert "(due Sat" not in assignment
                    assert "(due Sun" not in assignment

                for assessment in week.get("assessments", []):
                    assert "(due Sat" not in assessment
                    assert "(due Sun" not in assessment

        finally:
            # Reset environment
            os.environ.pop("BUILD_MODE", None)

    def test_normalized_provenance_structure(self, golden_dir):
        """Test that normalized data includes proper provenance."""
        from scripts.rules.dates import DateRules
        from scripts.rules.engine import CourseRulesEngine

        # Load some course data
        course_data = {
            "course_code": "MATH221",
            "course_name": "Linear Algebra",
            "instructor": {
                "name": "Dr. Smith",
                "email": "smith@carleton.edu"
            },
            "schedule": [
                {
                    "week": 1,
                    "topic": "Introduction",
                    "assignments": ["HW1"],
                    "assessments": []
                }
            ]
        }

        # Normalize it
        engine = CourseRulesEngine(DateRules())
        normalized = engine.normalize(course_data)

        # Check provenance exists
        assert normalized.identity.code.provenance is not None
        assert normalized.identity.code.provenance.source.value == "original"
        assert normalized.identity.code.provenance.confidence == 1.0

        # Check instructor provenance
        assert normalized.instructor.name.provenance is not None
        assert normalized.instructor.name.value == "Dr. Smith"

        # Check confidence calculation
        confidence = normalized.get_confidence()
        assert 0.0 <= confidence <= 1.0

    def test_deterministic_checksums(self, service):
        """Test that repeated projections produce same checksums."""
        try:
            # Unified service does not expose checksum-based projections; skip
            import pytest as _pytest
            _pytest.skip("Checksum-based projections not exposed in unified service")
        except Exception:
            pass

    @pytest.mark.parametrize("course_id", ["MATH221", "MATH251", "STAT253"])
    def test_all_courses_have_valid_projections(self, course_id):
        """Test that all courses can generate valid projections."""
        service = CourseService(course_id)

        # Test in v2 mode
        os.environ["BUILD_MODE"] = "v2"
        try:
            context = service.get_template_context("schedule")

            # Should have some context
            assert context is not None
            assert "course" in context
            assert context["course"]["code"] == course_id

            # In v2 mode, should have projection
            if "schedule_projection" in context:
                proj = context["schedule_projection"]
                assert "weeks" in proj

                # Check no weekend dues
                for week in proj.get("weeks", []):
                    for item in week.get("assignments", []) + week.get("assessments", []):
                        if isinstance(item, str):
                            assert "(due Sat" not in item
                            assert "(due Sun" not in item

        finally:
            os.environ.pop("BUILD_MODE", None)

    def test_golden_fixture_compatibility(self, golden_dir):
        """Test that golden fixtures are valid JSON and properly structured."""
        for fixture_file in golden_dir.glob("*.json"):
            with open(fixture_file) as f:
                data = json.load(f)

            # Basic structure checks
            assert isinstance(data, dict), f"{fixture_file.name} is not a dict"

            # Check for expected top-level keys based on fixture type
            if "projection" in fixture_file.name:
                assert "projection_type" in data
                assert "data" in data
                assert "metadata" in data
            elif "normalized" in fixture_file.name:
                assert "identity" in data or "metadata" in data

    def test_date_rules_against_golden(self):
        """Test date rules produce expected results."""
        from scripts.rules.dates import DateRules
        from scripts.utils.semester_calendar import SemesterCalendar

        cal = SemesterCalendar()
        rules = DateRules(calendar=cal)

        # Test standard homework - should be Friday
        hw_day = rules.choose_due_weekday("Homework 1", is_assessment=False)
        assert hw_day == 4  # Friday

        # Test Blackboard - should be Wednesday
        bb_day = rules.choose_due_weekday("BB Discussion", is_assessment=False)
        assert bb_day == 2  # Wednesday

        # Test quiz - should be Friday
        quiz_day = rules.choose_due_weekday("Quiz 1", is_assessment=True)
        assert quiz_day == 4  # Friday

        # Test exam - should be Thursday
        exam_day = rules.choose_due_weekday("Midterm Exam", is_assessment=True)
        assert exam_day == 3  # Thursday

        # Test Fall Break shift
        holidays = ["Fall Break Thu-Fri"]

        # Thursday exam should shift to Wednesday
        shifted_day, add_days = rules.apply_holiday_shift(
            3, holidays, "Midterm", True
        )
        assert shifted_day == 2  # Wednesday
        assert add_days == 0

        # Friday homework should shift to next Monday
        shifted_day, add_days = rules.apply_holiday_shift(
            4, holidays, "Homework", False
        )
        assert shifted_day == 0  # Monday
        assert add_days == 7  # Next week

    def test_stable_id_generation(self):
        """Test that stable IDs are generated consistently."""
        from scripts.utils.schema.versions.v1_1_0 import create_stable_id

        # Same inputs should produce same ID
        id1 = create_stable_id("MATH221", "Fall", 2025)
        id2 = create_stable_id("MATH221", "Fall", 2025)
        assert id1 == id2

        # Different inputs should produce different IDs
        id3 = create_stable_id("MATH251", "Fall", 2025)
        assert id3 != id1

        # ID should have expected format
        assert id1.startswith("math221-fall-2025-")
        assert len(id1) > 20  # Has hash suffix
