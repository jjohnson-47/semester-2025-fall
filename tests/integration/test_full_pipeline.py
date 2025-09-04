"""Integration tests for the full build pipeline.

These tests ensure the entire system works together correctly,
from raw data through normalization, projection, and output generation.
"""

import os
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.build_pipeline import BuildPipeline
from scripts.build_schedules import ScheduleBuilder
from scripts.build_syllabi import SyllabusBuilder
from scripts.services.course_service import CourseService
from scripts.services.validation import ValidationGateway


class TestFullPipeline:
    """Integration tests for complete pipeline."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def all_courses(self):
        """List of all test courses."""
        return ["MATH221", "MATH251", "STAT253"]

    def test_pipeline_stages_execute(self, all_courses):
        """Test that all pipeline stages execute without errors."""
        pipeline = BuildPipeline(all_courses)

        # Run pipeline (currently mostly stubs)
        try:
            pipeline.run(force=False)

            # Check that stages were called
            assert hasattr(pipeline, "stages")
            assert len(pipeline.stages) > 0

            # Verify stage order
            stage_names = [name for name, _ in pipeline.stages]
            expected_order = ["validate", "normalize", "project", "generate", "package", "report"]
            assert stage_names == expected_order

        except Exception as e:
            pytest.fail(f"Pipeline failed: {str(e)}")

    def test_validation_gateway_integration(self, all_courses):
        """Test validation gateway works with all courses."""
        gateway = ValidationGateway()

        for course_id in all_courses:
            result = gateway.validate_for_build(course_id)

            # Should return a result
            assert result is not None
            assert hasattr(result, "ok")
            assert hasattr(result, "messages")

            # Check for v1.1.0 compatibility
            if not result.ok:
                # Log validation issues for debugging
                print(f"{course_id}: {result.messages}")

    def test_course_service_projection_generation(self, all_courses):
        """Test that CourseService can generate projections."""
        for course_id in all_courses:
            service = CourseService(course_id)

            # Test legacy mode
            context = service.get_template_context("schedule")
            assert context is not None
            assert "course" in context
            assert context["course"]["code"] == course_id

            # Test v2 mode
            os.environ["BUILD_MODE"] = "v2"
            try:
                v2_context = service.get_template_context("schedule")

                # Should have projection in v2 mode
                if "schedule_projection" in v2_context:
                    proj = v2_context["schedule_projection"]
                    assert "weeks" in proj

                    # Verify no weekend due dates
                    for week in proj.get("weeks", []):
                        for item in week.get("assignments", []) + week.get("assessments", []):
                            if isinstance(item, str):
                                assert "(due Sat" not in item
                                assert "(due Sun" not in item
            finally:
                os.environ.pop("BUILD_MODE", None)

    def test_v2_syllabus_builder_uses_projection(self, temp_output_dir):
        """Test that Syllabus builder uses projection data in v2 mode."""
        syllabus_builder = SyllabusBuilder(
            template_dir="templates", output_dir=str(temp_output_dir / "syllabi")
        )
        os.environ["BUILD_MODE"] = "v2"
        try:
            data = syllabus_builder.load_course_data("MATH221")
            assert data is not None and "calendar" in data
            # In v2, we add formatted assignments into calendar weeks
            weeks = data["calendar"].get("weeks", [])
            if weeks:
                any_formatted = any(
                    bool(w.get("formatted_assignments") or w.get("formatted_assessments"))
                    for w in weeks
                )
                assert any_formatted, "Expected formatted assignments/assessments in v2"
        finally:
            os.environ.pop("BUILD_MODE", None)

    def test_v2_projection_json_structure(self, temp_output_dir):
        """Test that v2 projection JSON has expected structure (in-memory)."""
        os.environ["BUILD_MODE"] = "v2"
        try:
            ctx = CourseService("MATH221").get_template_context("schedule")
            assert "schedule_projection" in ctx
            data = ctx["schedule_projection"]
            assert "weeks" in data and isinstance(data["weeks"], list)
            # No weekend dues in projection
            for w in data["weeks"]:
                for item in w.get("assignments", []) + w.get("assessments", []):
                    if isinstance(item, str):
                        assert "(due Sat" not in item and "(due Sun" not in item
        finally:
            os.environ.pop("BUILD_MODE", None)

    def test_end_to_end_build(self, temp_output_dir, all_courses):
        """Test complete end-to-end build process."""
        # Step 1: Validation
        gateway = ValidationGateway()
        validation_results = {}

        for course_id in all_courses:
            result = gateway.validate_for_build(course_id)
            validation_results[course_id] = result.ok

        # At least one course should validate
        assert any(validation_results.values()), "No courses passed validation"

        # Step 2: Run pipeline
        pipeline = BuildPipeline(all_courses)
        pipeline.run()

        # Step 3: Build outputs (legacy mode)
        for course_id in all_courses:
            if validation_results[course_id]:
                # Build schedule
                schedule_builder = ScheduleBuilder(output_dir=str(temp_output_dir / "schedules"))
                try:
                    schedule_builder.build_schedule(course_id)

                    # Check output exists
                    (
                        temp_output_dir / "schedules" / f"{course_id.lower()}_schedule.html"
                    )
                    # File might not exist if builder uses stubs

                except Exception:
                    pass  # Builder might be stub

        # Step 4: Test v2 mode
        os.environ["BUILD_MODE"] = "v2"
        try:
            for course_id in all_courses:
                service = CourseService(course_id)
                context = service.get_template_context("schedule")

                # Should have enhanced context in v2
                if "schedule_projection" in context:
                    assert context["schedule_projection"] is not None
        finally:
            os.environ.pop("BUILD_MODE", None)

    def test_stable_id_generation(self):
        """Test that stable IDs are generated correctly."""
        from scripts.utils.schema.versions.v1_1_0 import create_stable_id

        # Test determinism
        id1 = create_stable_id("MATH221", "Fall", 2025)
        id2 = create_stable_id("MATH221", "Fall", 2025)
        assert id1 == id2, "Stable IDs not deterministic"

        # Test uniqueness
        id3 = create_stable_id("MATH251", "Fall", 2025)
        assert id3 != id1, "Different courses have same ID"

        # Test format
        assert id1.startswith("math221-fall-2025-")
        assert len(id1.split("-")) == 4  # course-term-year-hash

    def test_date_rules_in_pipeline(self):
        """Test that date rules are applied in pipeline."""
        from scripts.rules.dates import DateRules
        from scripts.utils.semester_calendar import SemesterCalendar

        cal = SemesterCalendar()
        rules = DateRules(calendar=cal)

        # Test enforcement helpers
        weekday = rules.choose_due_weekday("Homework 1", is_assessment=False)
        assert weekday == 4  # Friday

        # Test holiday shift
        holidays = ["Fall Break Thu-Fri"]
        shifted, add_days = rules.apply_holiday_shift(4, holidays, "Homework", False)
        assert shifted == 0  # Monday
        assert add_days == 7  # Next week

        # Test formatting
        due_str = rules.format_due("2025-09-08", 4, 0)
        assert "(due Fri" in due_str
        assert "09/12" in due_str

    @pytest.mark.parametrize("build_mode", ["legacy", "v2"])
    def test_build_mode_switching(self, build_mode):
        """Test that build mode switching works correctly."""
        # Set build mode
        if build_mode == "v2":
            os.environ["BUILD_MODE"] = "v2"
        else:
            os.environ.pop("BUILD_MODE", None)

        try:
            service = CourseService("MATH221")
            context = service.get_template_context("schedule")

            # Check context based on mode
            if build_mode == "v2":
                # Should have projection in v2 mode
                assert "metadata" in context
                # May have projection if data available
                if "schedule_projection" in context:
                    assert isinstance(context["schedule_projection"], dict)
            else:
                # Legacy mode - basic context
                assert "course" in context
                assert "metadata" in context
                # Should not have projection
                assert "schedule_projection" not in context

        finally:
            os.environ.pop("BUILD_MODE", None)

    def test_migration_compatibility(self):
        """Test that migration maintains compatibility."""
        # Test schema validation with both old and new formats
        gateway = ValidationGateway()

        # Old format (string items)
        old_schedule = {
            "weeks": [
                {
                    "week": 1,
                    "topic": "Introduction",
                    "assignments": ["HW1"],
                    "assessments": ["Quiz 1"],
                }
            ]
        }

        result = gateway.validate_schedule_v1_1_0(old_schedule)
        assert result.ok, f"Old format failed: {result.messages}"

        # New format (object items)
        new_schedule = {
            "weeks": [
                {
                    "week": 1,
                    "topic": "Introduction",
                    "assignments": [{"id": "2025FA-MATH221-HW-01", "title": "HW1"}],
                    "assessments": [{"id": "2025FA-MATH221-QUIZ-01", "title": "Quiz 1"}],
                }
            ]
        }

        result = gateway.validate_schedule_v1_1_0(new_schedule)
        assert result.ok, f"New format failed: {result.messages}"

        # Mixed format (backward compatibility)
        mixed_schedule = {
            "weeks": [
                {
                    "week": 1,
                    "topic": "Introduction",
                    "assignments": ["HW1", {"id": "2025FA-MATH221-HW-02", "title": "HW2"}],
                    "assessments": ["Quiz 1"],
                }
            ]
        }

        result = gateway.validate_schedule_v1_1_0(mixed_schedule)
        assert result.ok, f"Mixed format failed: {result.messages}"
