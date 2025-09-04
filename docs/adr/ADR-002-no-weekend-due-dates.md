# ADR-002: No Weekend Due Dates Policy

## Status
Accepted

## Context

Students and instructors have reported issues with weekend due dates:
- Reduced availability for help
- Work-life balance concerns
- Technical support unavailable
- Inconsistent handling across courses

Currently, due dates are manually set and may fall on weekends, leading to ad-hoc adjustments and confusion.

## Decision

Implement a systematic "No Weekend Due Dates" policy enforced through the DateRules engine:

1. **Automatic Adjustment**: Weekend dates shift to preceding Friday
2. **Holiday Handling**: Dates on holidays shift based on assignment type
3. **Centralized Logic**: All date adjustments go through DateRules
4. **Configurable Behavior**: Different rules for different assignment types

## Implementation

```python
class DateRules:
    def apply_rules(self, date: datetime, assignment_type: AssignmentType) -> datetime:
        # Weekend rule
        if self.is_weekend(date):
            date = self.shift_from_weekend(date, direction="before")
        
        # Holiday rule
        if self.is_holiday(date):
            date = self.shift_for_holiday(date, direction="auto")
        
        return date
```

### Assignment Type Handling

- **HOMEWORK**: Shift to Friday before
- **QUIZ**: Shift to Friday before
- **EXAM**: May require manual review
- **PROJECT**: Shift to Friday before
- **OTHER**: Default to Friday before

## Consequences

### Positive

- **Consistency**: All courses follow same rules
- **Student-Friendly**: Respects work-life balance
- **Predictable**: Students know dates won't be on weekends
- **Automated**: No manual adjustment needed
- **Auditable**: All adjustments tracked via provenance

### Negative

- **Calendar Compression**: More due dates on Fridays
- **Scheduling Conflicts**: Multiple assignments may cluster
- **Holiday Complexity**: Holidays require special handling
- **Legacy Data**: Historical dates need migration

## Alternatives Considered

### 1. Monday Due Dates
Shift weekend dates to following Monday.
- ❌ Extends deadlines unexpectedly
- ❌ Monday clustering problem
- ❌ Start-of-week stress

### 2. Manual Override Only
Allow instructors to manually avoid weekends.
- ❌ Inconsistent application
- ❌ Human error prone
- ❌ No systematic enforcement

### 3. No Adjustment
Keep dates as specified, including weekends.
- ❌ Current problem persists
- ❌ Student dissatisfaction
- ❌ Support burden

## Migration

1. **Identify Weekend Dates**: Scan all existing schedules
2. **Apply Rules**: Use DateRules to adjust
3. **Track Changes**: Log all adjustments with provenance
4. **Notify Instructors**: Report adjusted dates

## Validation

The ValidationGateway checks for:
- No assignments due on weekends
- Proper holiday handling
- Consistent application across weeks
- Provenance for all adjustments

## Rollback

If policy needs reversal:
1. Disable DateRules in CourseRulesEngine
2. Restore original dates from provenance
3. Mark policy as deprecated

## Metrics

- Weekend due dates: Target 0
- Date adjustments tracked: 100%
- Instructor overrides: <5%
- Student complaints about due dates: Reduce by 50%

## References

- [dates_full.py](../../scripts/rules/dates_full.py)
- [MIGRATION_GUIDE.md](../MIGRATION_GUIDE.md)