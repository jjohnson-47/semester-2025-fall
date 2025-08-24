# Due Dates System Documentation

## Overview

The due dates system provides a single source of truth for assignment and assessment due dates across all courses. It supports both automatically calculated dates based on the academic calendar and custom dates from external systems (e.g., Pearson MyLab, McGraw-Hill Connect).

## Architecture

### File Structure

```
content/courses/{COURSE_CODE}/
├── schedule.json         # Primary schedule with topics and assignments
└── due_dates.json       # Optional: Custom due dates override
```

### Due Dates Priority (Single Source of Truth)

1. **Custom Due Dates** (`due_dates.json`) - Highest priority, used when present
2. **Auto-calculated** - Default fallback based on week patterns

## Custom Due Dates Format

### Schema: `due_dates.json`

```json
{
  "description": "Brief description of what this contains",
  "source": "External system name (e.g., Pearson MyLab Statistics)",
  "last_updated": "YYYY-MM-DD",
  "dates": {
    "Assignment Name": "YYYY-MM-DD",
    "Test Name": "YYYY-MM-DD"
  }
}
```

### Example

```json
{
  "description": "Custom due dates for STAT253 assignments and assessments",
  "source": "Pearson MyLab Statistics - Fall 2025",
  "last_updated": "2025-08-23",
  "dates": {
    "Homework #1 - Chapter 1": "2025-08-29",
    "Chapter 1 Test": "2025-09-02",
    "R Assignment 1": "2025-09-05"
  }
}
```

## Integration Points

### Schedule Builder

The `ScheduleBuilder` class in `scripts/build_schedules.py`:

1. Loads custom due dates if `due_dates.json` exists
2. Matches assignment names from `schedule.json` with custom dates
3. Falls back to auto-calculated dates when no match found
4. Logs the source of dates for transparency

### Syllabus Builder

The `SyllabusBuilder` class in `scripts/build_syllabi.py`:

1. Receives schedule data with resolved due dates
2. Displays dates in weekly schedule table
3. Maintains consistency with schedule output

## Adding Custom Due Dates

### For External Systems (MyLab, Connect, etc.)

1. Export due dates from the external system
2. Create `content/courses/{COURSE_CODE}/due_dates.json`
3. Format according to schema above
4. Run build scripts to apply dates

### Naming Conventions

Assignment names in `due_dates.json` must **exactly match** those in `schedule.json`:

- ✅ "Homework #1 - Chapter 1" (matches)
- ❌ "HW1 Chapter 1" (won't match)
- ❌ "Homework 1 - Ch 1" (won't match)

## Archival Reference

Original external system exports are preserved in `docs/archive/` for reference:

- `stat253-mylab-schedule.json` - Original Pearson MyLab export

## Best Practices

1. **Update Frequency**: Review and update custom due dates at semester start
2. **Source Documentation**: Always include source and last_updated fields
3. **Name Consistency**: Ensure assignment names match exactly between files
4. **Version Control**: Commit due date changes with clear messages
5. **Testing**: Run build scripts after updates to verify correct application

## Troubleshooting

### Dates Not Applying

- Check assignment name matches exactly (case-sensitive)
- Verify date format is YYYY-MM-DD
- Ensure JSON is valid (no trailing commas)
- Check build script output for loading confirmation

### Missing Dates

- System will auto-calculate based on week patterns
- Check build logs for "Using custom due dates from:" message
- Verify `due_dates.json` exists in correct location

## Future Enhancements

- [ ] Validation tool to check name matching
- [ ] Import scripts for common LMS formats
- [ ] Due date conflict detection
- [ ] Automatic reminder generation
