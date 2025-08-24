# MATH221 Schedule Update Summary

## Overview

Successfully updated MATH221 (Applied Calculus) to conform to established schedule standards with specific MyOpenMath assignments, Blackboard discussions, and exam dates.

## Changes Implemented

### 1. Schedule Structure (`schedule.json`)

- **15 weeks of instruction** with detailed topics matching the syllabus
- **MyOpenMath assignments** for each section covered
- **Blackboard discussions** for each week
- **3 midterm exams** with specific coverage and timing
- **Final exam** during finals week

### 2. Custom Due Dates (`due_dates.json`)

Created authoritative due dates file with:

- **Source**: MyOpenMath - Applied Calculus Course
- **All assignments** with Friday due dates (except Week 14 - Monday after Thanksgiving)
- **Exam dates**:
  - Exam #1: October 1 (Wednesday)
  - Exam #2: October 29 (Wednesday)
  - Exam #3: November 26 (Wednesday)
  - Final Exam: December 10 (Wednesday)

### 3. Evaluation Tools Update

Clarified grading breakdown:

- Blackboard Discussion Participation: 4%
- MyOpenMath Homework: 24%
- MyOpenMath Class Activities: 12%
- Exams (3 Midterms @ 15% each): 45%
- Final Exam: 15%

## Schedule Highlights

### Week-by-Week Coverage

- **Weeks 1-5**: Functions through Derivative Formulas
- **Week 6**: Exam #1 (covers Sections 1.1-2.4)
- **Weeks 7-9**: Applications of Derivatives
- **Week 10**: Exam #2 (covers Sections 2.5-2.11)
- **Weeks 11-13**: Integration and Applications
- **Week 14**: Exam #3 (covers Sections 3.1-3.8) + Thanksgiving
- **Week 15**: Multivariable Calculus Introduction
- **Finals Week**: Comprehensive Final (Sections 2.5-4.3)

### Key Features

- **Consistent Friday due dates** for homework and discussions
- **48-hour exam windows** (Monday open, Wednesday close)
- **Holiday accommodations** (Labor Day, Thanksgiving)
- **Clear section coverage** for each assignment

## Testing Verification

✅ All 15 MyOpenMath assignments appear in schedule
✅ All 15 Blackboard discussions listed
✅ All 4 exams (3 midterms + final) with correct dates
✅ Topics flow through to syllabus
✅ CSS styling applied correctly
✅ Custom due dates loaded successfully

## File Structure

```
content/courses/MATH221/
├── schedule.json          # Updated with detailed weekly content
├── due_dates.json        # New - custom MyOpenMath due dates
├── evaluation_tools.json # Updated with clearer breakdown
└── [other course files]
```

## Build Output

```
build/schedules/MATH221_schedule.html  # HTML schedule with all assignments
build/schedules/MATH221_schedule.md    # Markdown version
build/syllabi/MATH221.html            # Syllabus with integrated schedule
```

## Consistency with STAT253

MATH221 now follows the same patterns as STAT253:

- Single source of truth for due dates
- Consistent data flow from schedule to syllabus
- Proper CSS architecture integration
- Clear assessment tracking

## Dashboard Integration

The schedule is fully integrated with the dashboard:

- Viewable at `/schedules/MATH221`
- Syllabus at `/syllabi/MATH221`
- CSS properly served and applied
- Topics and assignments display correctly
