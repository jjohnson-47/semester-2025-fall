"""Compatibility facade for DateRules (pre-refactor path).

Bridges the feature branch API to the current rules engine implementation by
re-exporting the modern DateRules and providing matching enum/dataclass types.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

# Reuse AssignmentType from the unified models
from scripts.rules.models import AssignmentType  # noqa: F401
from scripts.rules.dates import DateRules as _DateRules


class ShiftDirection(Enum):
  EARLIER = "earlier"
  LATER = "later"
  NEAREST = "nearest"


@dataclass
class DateShift:
  original: datetime
  shifted: datetime
  reason: str
  rule: str


class DateRules(_DateRules):  # type: ignore[misc]
  """Subclass for compatibility; inherits full functionality from current rules.

  This preserves import paths used by the feature branch while relying on the
  consolidated implementation in `scripts/rules/dates.py`.
  """

  # No additional behavior needed; all features are in the parent implementation.
  pass
            AssignmentType.PAPER: {"preferred_day": 1, "shift": ShiftDirection.EARLIER},  # Monday
        }
    
    def _load_holidays(self) -> Set[datetime]:
        """Load holidays from calendar.
        
        Returns:
            Set of holiday dates
        """
        holidays = set()
        
        # Get holidays from semester calendar
        weeks = self.calendar.get_weeks()
        for week in weeks:
            if week.get("holidays"):
                # Add holiday dates (these are already datetime objects)
                start = datetime.strptime(week["start"], "%Y-%m-%d")
                # Common holidays
                holiday_names = week["holidays"]
                for holiday in holiday_names:
                    if "Labor Day" in holiday:
                        # First Monday of September
                        holidays.add(start)
                    elif "Thanksgiving" in holiday:
                        # Fourth Thursday of November and Friday
                        holidays.add(start)
                        holidays.add(start + timedelta(days=1))
                    elif "Fall Break" in holiday:
                        # Typically Thursday-Friday
                        holidays.add(start + timedelta(days=3))
                        holidays.add(start + timedelta(days=4))
        
        return holidays
    
    def is_weekend(self, date: datetime) -> bool:
        """Check if date falls on weekend.
        
        Args:
            date: Date to check
            
        Returns:
            True if Saturday (5) or Sunday (6)
        """
        return date.weekday() >= 5
    
    def is_holiday(self, date: datetime) -> bool:
        """Check if date is a holiday.
        
        Args:
            date: Date to check
            
        Returns:
            True if date is a holiday
        """
        # Normalize to date only
        date_only = date.replace(hour=0, minute=0, second=0, microsecond=0)
        return date_only in self.holidays
    
    def is_valid_due_date(self, date: datetime) -> bool:
        """Check if date is valid for assignments.
        
        Args:
            date: Date to check
            
        Returns:
            True if date is valid (not weekend or holiday)
        """
        return not self.is_weekend(date) and not self.is_holiday(date)
    
    def shift_from_weekend(self, date: datetime, 
                          direction: ShiftDirection = ShiftDirection.EARLIER) -> datetime:
        """Shift weekend dates to nearest weekday.
        
        Args:
            date: Original date
            direction: Direction to shift
            
        Returns:
            Shifted date (Friday if earlier, Monday if later)
        """
        if not self.is_weekend(date):
            return date
        
        original = date
        if date.weekday() == 5:  # Saturday
            if direction == ShiftDirection.EARLIER:
                date = date - timedelta(days=1)  # Friday
            else:
                date = date + timedelta(days=2)  # Monday
        elif date.weekday() == 6:  # Sunday
            if direction == ShiftDirection.EARLIER:
                date = date - timedelta(days=2)  # Friday
            else:
                date = date + timedelta(days=1)  # Monday
        
        # Log the shift
        self.shift_log.append(DateShift(
            original=original,
            shifted=date,
            reason="Weekend shift",
            rule="no_weekend_due_dates"
        ))
        
        return date
    
    def shift_for_holiday(self, date: datetime,
                         direction: ShiftDirection = ShiftDirection.EARLIER) -> datetime:
        """Shift dates that fall on holidays.
        
        Args:
            date: Original date
            direction: Direction to shift
            
        Returns:
            Shifted date (earlier or later based on direction)
        """
        if not self.is_holiday(date):
            return date
        
        original = date
        shift_days = 1 if direction == ShiftDirection.LATER else -1
        
        # Keep shifting until we find a valid date
        shifted = date
        attempts = 0
        while (self.is_holiday(shifted) or self.is_weekend(shifted)) and attempts < 7:
            shifted = shifted + timedelta(days=shift_days)
            attempts += 1
        
        # If we couldn't find a good date, try the other direction
        if attempts >= 7:
            shift_days = -shift_days
            shifted = date
            attempts = 0
            while (self.is_holiday(shifted) or self.is_weekend(shifted)) and attempts < 7:
                shifted = shifted + timedelta(days=shift_days)
                attempts += 1
        
        # Log the shift
        self.shift_log.append(DateShift(
            original=original,
            shifted=shifted,
            reason="Holiday accommodation",
            rule="holiday_shift_policy"
        ))
        
        return shifted
    
    def apply_rules(self, date: datetime, 
                   assignment_type: AssignmentType = AssignmentType.OTHER) -> datetime:
        """Apply all date rules to ensure valid due date.
        
        Args:
            date: Original date
            assignment_type: Type of assignment
            
        Returns:
            Valid due date after applying all rules
        """
        # Get preferences for this assignment type
        prefs = self.type_preferences.get(assignment_type, {
            "shift": ShiftDirection.EARLIER
        })
        direction = prefs["shift"]
        
        # Apply weekend rule first
        if self.is_weekend(date):
            date = self.shift_from_weekend(date, direction)
        
        # Then apply holiday rule
        if self.is_holiday(date):
            date = self.shift_for_holiday(date, direction)
        
        # Final check - ensure we have a valid date
        if not self.is_valid_due_date(date):
            # Emergency fallback - find nearest valid date
            for offset in range(1, 8):
                earlier = date - timedelta(days=offset)
                later = date + timedelta(days=offset)
                
                if self.is_valid_due_date(earlier):
                    date = earlier
                    break
                if self.is_valid_due_date(later):
                    date = later
                    break
        
        return date
    
    def get_preferred_day(self, assignment_type: AssignmentType,
                         week_start: datetime) -> datetime:
        """Get preferred due date for assignment type in a given week.
        
        Args:
            assignment_type: Type of assignment
            week_start: Monday of the target week
            
        Returns:
            Preferred due date (with rules applied)
        """
        prefs = self.type_preferences.get(assignment_type, {})
        preferred_day = prefs.get("preferred_day", 5)  # Default to Friday
        
        # Calculate target date
        target = week_start + timedelta(days=preferred_day)
        
        # Apply rules to ensure validity
        return self.apply_rules(target, assignment_type)
    
    def validate_schedule(self, dates: List[datetime]) -> List[str]:
        """Validate a list of dates against rules.
        
        Args:
            dates: List of dates to validate
            
        Returns:
            List of validation errors (empty if all valid)
        """
        errors = []
        
        for date in dates:
            if self.is_weekend(date):
                errors.append(f"Date {date.strftime('%Y-%m-%d')} falls on weekend")
            if self.is_holiday(date):
                errors.append(f"Date {date.strftime('%Y-%m-%d')} falls on holiday")
        
        return errors
    
    def get_shift_report(self) -> Dict[str, any]:
        """Get report of all date shifts performed.
        
        Returns:
            Report with shift statistics and details
        """
        return {
            "total_shifts": len(self.shift_log),
            "weekend_shifts": sum(1 for s in self.shift_log if "Weekend" in s.reason),
            "holiday_shifts": sum(1 for s in self.shift_log if "Holiday" in s.reason),
            "shifts": [
                {
                    "original": s.original.isoformat(),
                    "shifted": s.shifted.isoformat(),
                    "reason": s.reason,
                    "rule": s.rule
                }
                for s in self.shift_log
            ]
        }
