# MATH251 Schedule Update Summary

## Overview

Successfully converted MATH251 (Calculus I) raw schedule to conform to established project standards with Edfinity assignments, Blackboard discussions, weekly quizzes, and written problems.

## Changes Implemented

### 1. Schedule Structure (`schedule.json`)

- **15 weeks of instruction** with detailed calculus topics
- **Edfinity homework** for each section covered
- **Blackboard discussions** (BB1-BB14) for key concepts
- **Weekly quizzes** (13 total - no Week 9 quiz)
- **5 Written Problems** assignments on Mondays
- **Midterm exam** in Week 8
- **Final exam** during finals week

### 2. Custom Due Dates (`due_dates.json`)

Created authoritative due dates file with:

- **Source**: Edfinity - Calculus I Course
- **Regular assignments**: Friday 11:59 PM due dates
- **Written Problems**: Monday 11:59 PM due dates
  - Written Problems #1: September 15
  - Written Problems #2: October 6
  - Written Problems #3: October 20
  - Written Problems #4: November 3
  - Written Problems #5: November 17
- **Midterm**: October 20 (Monday)
- **Final Exam**: December 12 (Friday)
- **Week 14 adjustments**: Wednesday due date for Thanksgiving week

### 3. Course Content Organization

#### Unit 1: Limits and Continuity (Weeks 1-2)

- Measuring velocity, notion of limits
- Finding limits, continuity

#### Unit 2: Derivative Concepts (Weeks 3-8)

- Derivative at a point and derivative function
- Interpreting derivatives, second derivatives
- Tangent lines, derivative rules
- Trig derivatives, product/quotient rules
- Chain rule, inverse functions
- Implicit differentiation
- **Midterm Exam** (end of Week 8)

#### Unit 3: Derivative Applications (Weeks 9-11)

- L'Hôpital's Rule, extreme values
- Optimization
- Applied optimization, related rates

#### Unit 4: Integration (Weeks 12-15)

- Riemann sums, definite integral
- Fundamental Theorem of Calculus
- Integration techniques
- Review and final preparation

## Key Features

### Assessment Structure

- **Weekly Quizzes**: 13 quizzes (Week 9 exception)
- **Written Problems**: 5 assignments throughout semester
- **Blackboard Discussions**: 14 conceptual discussions
- **Edfinity Homework**: Section-specific assignments
- **Exams**: 1 Midterm + 1 Final (both proctored)

### Date Verification

✅ All Friday due dates confirmed
✅ Monday dates for Written Problems verified
✅ Holiday accommodations (Labor Day, Thanksgiving)
✅ Withdrawal deadline noted (October 31)

## Testing Verification

✅ 14 Edfinity assignments appear in schedule
✅ 5 Written Problems with correct Monday dates
✅ 13 Weekly Quizzes (no Week 9)
✅ Midterm and Final exams properly placed
✅ Topics flow through to syllabus
✅ CSS styling applied correctly
✅ Custom due dates loaded successfully

## File Structure

```
content/courses/MATH251/
├── schedule.json          # Updated with detailed weekly content
├── due_dates.json        # New - custom Edfinity due dates
├── evaluation_tools.json # Existing grading breakdown
└── [other course files]
```

## Build Output

```
build/schedules/MATH251_schedule.html  # HTML schedule with all assignments
build/schedules/MATH251_schedule.md    # Markdown version
build/syllabi/MATH251.html            # Syllabus with integrated schedule
```

## Consistency with Project Standards

MATH251 now follows the same patterns as STAT253 and MATH221:

- Single source of truth for due dates
- Consistent data flow from schedule to syllabus
- Proper CSS architecture integration
- Clear assessment tracking with specific due dates

## Dashboard Integration

The schedule is fully integrated with the dashboard:

- Viewable at `/schedules/MATH251`
- Syllabus at `/syllabi/MATH251`
- CSS properly served and applied
- All assignments display with correct dates

## Important Notes

- Week 9 has no quiz (as specified in raw schedule)
- Written Problems have Monday due dates (different from regular Friday pattern)
- Week 14 assignments due Wednesday (before Thanksgiving)
- All dates verified against 2025 calendar
