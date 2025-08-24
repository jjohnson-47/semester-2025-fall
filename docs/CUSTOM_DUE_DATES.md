# Custom Due Dates System

## Overview

The schedule builder supports custom due dates for any course that needs to override the automatic date calculation. This is useful when courses use external systems (MyLab, WebAssign, etc.) with pre-set due dates.

## How to Use

### 1. Create a Due Dates File

For any course that needs custom dates, create a file at:

```
content/courses/{COURSE_CODE}/due_dates.json
```

### 2. File Format

The file should follow this structure:

```json
{
  "description": "Brief description of what these dates are for",
  "source": "Source system (e.g., 'Pearson MyLab Statistics - Fall 2025')",
  "last_updated": "YYYY-MM-DD",
  "dates": {
    "Assignment Name": "YYYY-MM-DD",
    "Test Name": "YYYY-MM-DD",
    ...
  }
}
```

### 3. How It Works

- When building a schedule, the builder checks for `due_dates.json`
- If found, it uses those dates instead of calculating automatically
- The source is logged during build for transparency
- Dates are formatted with day of week (e.g., "due Mon 09/08")

### 4. Example: STAT253

See `content/courses/STAT253/due_dates.json` for a complete example with:

- Homework assignments with specific MyLab due dates
- Chapter tests on their official dates
- R assignments and Final Report drafts
- All dates in ISO format (YYYY-MM-DD)

### 5. Benefits

- **Extensible**: Any course can use this system
- **Transparent**: Source is documented and logged
- **Flexible**: Mix custom and automatic dates
- **Maintainable**: Single source of truth for due dates
- **Version controlled**: Changes are tracked in git

### 6. Adding Custom Dates to a New Course

1. Export dates from your LMS or external system
2. Create `content/courses/{COURSE}/due_dates.json`
3. Map assignment/test names exactly as they appear in `schedule.json`
4. Run `python scripts/build_schedules.py --course {COURSE}`
5. Verify dates in the generated schedule

### 7. Updating Dates

When dates change:

1. Update the `due_dates.json` file
2. Update `last_updated` field
3. Rebuild the schedule
4. The dashboard will automatically show the new dates

## Technical Details

The implementation is in `scripts/build_schedules.py`:

- `_load_custom_due_dates()`: Loads the JSON file if it exists
- `_format_custom_due_date()`: Formats dates consistently
- Custom dates take precedence over automatic calculation
- Works for both assignments and assessments
- Handles finals week assessments too

## Future Enhancements

Potential improvements:

- Import directly from LMS APIs
- Validate dates against semester calendar
- Bulk update tool for multiple courses
- Conflict detection between courses
