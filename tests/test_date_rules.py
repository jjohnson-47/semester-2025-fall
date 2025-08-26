"""Tests for DateRules - the centralized date authority."""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.rules.dates_full import DateRules, AssignmentType, ShiftDirection, DateShift


class TestDateRules:
    """Test suite for DateRules."""
    
    @pytest.fixture
    def date_rules(self):
        """Create DateRules instance for testing."""
        return DateRules()
    
    def test_weekend_detection(self, date_rules):
        """Test weekend detection."""
        # Monday
        monday = datetime(2025, 9, 1)
        assert not date_rules.is_weekend(monday)
        
        # Friday
        friday = datetime(2025, 9, 5)
        assert not date_rules.is_weekend(friday)
        
        # Saturday
        saturday = datetime(2025, 9, 6)
        assert date_rules.is_weekend(saturday)
        
        # Sunday
        sunday = datetime(2025, 9, 7)
        assert date_rules.is_weekend(sunday)
    
    def test_shift_from_weekend_earlier(self, date_rules):
        """Test shifting weekend dates to earlier (Friday)."""
        # Saturday -> Friday
        saturday = datetime(2025, 9, 6)
        shifted = date_rules.shift_from_weekend(saturday, ShiftDirection.EARLIER)
        assert shifted.weekday() == 4  # Friday
        assert shifted == datetime(2025, 9, 5)
        
        # Sunday -> Friday
        sunday = datetime(2025, 9, 7)
        shifted = date_rules.shift_from_weekend(sunday, ShiftDirection.EARLIER)
        assert shifted.weekday() == 4  # Friday
        assert shifted == datetime(2025, 9, 5)
    
    def test_shift_from_weekend_later(self, date_rules):
        """Test shifting weekend dates to later (Monday)."""
        # Saturday -> Monday
        saturday = datetime(2025, 9, 6)
        shifted = date_rules.shift_from_weekend(saturday, ShiftDirection.LATER)
        assert shifted.weekday() == 0  # Monday
        assert shifted == datetime(2025, 9, 8)
        
        # Sunday -> Monday
        sunday = datetime(2025, 9, 7)
        shifted = date_rules.shift_from_weekend(sunday, ShiftDirection.LATER)
        assert shifted.weekday() == 0  # Monday
        assert shifted == datetime(2025, 9, 8)
    
    def test_no_shift_for_weekday(self, date_rules):
        """Test that weekdays are not shifted."""
        wednesday = datetime(2025, 9, 3)
        shifted = date_rules.shift_from_weekend(wednesday)
        assert shifted == wednesday
    
    def test_apply_rules_with_weekend(self, date_rules):
        """Test applying all rules to a weekend date."""
        saturday = datetime(2025, 9, 6)
        valid_date = date_rules.apply_rules(saturday, AssignmentType.HOMEWORK)
        
        # Should shift to Friday (earlier is default for homework)
        assert valid_date.weekday() == 4
        assert valid_date == datetime(2025, 9, 5)
    
    def test_get_preferred_day_homework(self, date_rules):
        """Test getting preferred day for homework (Friday)."""
        week_start = datetime(2025, 9, 1)  # Monday
        preferred = date_rules.get_preferred_day(AssignmentType.HOMEWORK, week_start)
        
        # Should be Friday of that week
        assert preferred.weekday() == 4
        assert preferred == datetime(2025, 9, 5)
    
    def test_get_preferred_day_exam(self, date_rules):
        """Test getting preferred day for exam (Thursday)."""
        week_start = datetime(2025, 9, 1)  # Monday
        preferred = date_rules.get_preferred_day(AssignmentType.EXAM, week_start)
        
        # Should be Thursday of that week
        assert preferred.weekday() == 3
        assert preferred == datetime(2025, 9, 4)
    
    def test_validate_schedule(self, date_rules):
        """Test schedule validation."""
        dates = [
            datetime(2025, 9, 1),  # Monday - valid
            datetime(2025, 9, 5),  # Friday - valid
            datetime(2025, 9, 6),  # Saturday - invalid
            datetime(2025, 9, 7),  # Sunday - invalid
        ]
        
        errors = date_rules.validate_schedule(dates)
        assert len(errors) == 2
        assert "weekend" in errors[0].lower()
        assert "weekend" in errors[1].lower()
    
    def test_shift_log_tracking(self, date_rules):
        """Test that shifts are logged for provenance."""
        saturday = datetime(2025, 9, 6)
        date_rules.shift_from_weekend(saturday)
        
        # Check shift was logged
        assert len(date_rules.shift_log) == 1
        shift = date_rules.shift_log[0]
        assert shift.original == saturday
        assert shift.shifted.weekday() == 4  # Friday
        assert "Weekend" in shift.reason
        assert shift.rule == "no_weekend_due_dates"
    
    def test_get_shift_report(self, date_rules):
        """Test shift report generation."""
        # Perform some shifts
        saturday = datetime(2025, 9, 6)
        sunday = datetime(2025, 9, 7)
        
        date_rules.shift_from_weekend(saturday)
        date_rules.shift_from_weekend(sunday)
        
        report = date_rules.get_shift_report()
        
        assert report["total_shifts"] == 2
        assert report["weekend_shifts"] == 2
        assert report["holiday_shifts"] == 0
        assert len(report["shifts"]) == 2


class TestDateRulesContracts:
    """Contract tests for DateRules invariants."""
    
    @pytest.fixture
    def date_rules(self):
        """Create DateRules instance for testing."""
        return DateRules()
    
    def test_contract_no_weekend_due_dates(self, date_rules):
        """CONTRACT: No due date should ever fall on a weekend."""
        # Generate dates for entire semester
        start = datetime(2025, 8, 25)
        dates_to_test = []
        
        for days in range(0, 120, 7):  # Every week for ~4 months
            for weekday in range(7):  # Every day of week
                test_date = start + timedelta(days=days + weekday)
                dates_to_test.append(test_date)
        
        # Apply rules to all dates
        for date in dates_to_test:
            result = date_rules.apply_rules(date)
            # CONTRACT: Result must never be weekend
            assert not date_rules.is_weekend(result), \
                f"Contract violation: {result} is a weekend date"
    
    def test_contract_deterministic_shifts(self, date_rules):
        """CONTRACT: Same input date must always produce same output."""
        saturday = datetime(2025, 9, 6)
        
        # Apply rules multiple times
        result1 = date_rules.apply_rules(saturday, AssignmentType.QUIZ)
        result2 = date_rules.apply_rules(saturday, AssignmentType.QUIZ)
        result3 = date_rules.apply_rules(saturday, AssignmentType.QUIZ)
        
        # CONTRACT: Must be deterministic
        assert result1 == result2 == result3
    
    def test_contract_shift_preserves_week(self, date_rules):
        """CONTRACT: Weekend shifts should stay in same week when possible."""
        # Saturday should shift to Friday (same week)
        saturday = datetime(2025, 9, 6)
        shifted = date_rules.shift_from_weekend(saturday, ShiftDirection.EARLIER)
        
        # Should be in same week (Friday)
        assert shifted < saturday
        assert (saturday - shifted).days <= 2
        
        # Sunday with LATER should go to Monday (next week ok)
        sunday = datetime(2025, 9, 7)
        shifted = date_rules.shift_from_weekend(sunday, ShiftDirection.LATER)
        
        # Should be Monday
        assert shifted > sunday
        assert (shifted - sunday).days == 1