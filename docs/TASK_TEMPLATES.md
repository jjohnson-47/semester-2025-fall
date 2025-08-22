# Task Template System Documentation

## Overview

The Task Template System provides a declarative way to define course preparation workflows using YAML templates. These templates automatically generate tasks with proper dependencies, due dates, and hierarchical relationships for multiple courses simultaneously.

## Template Structure

### Basic Template Format

```yaml
# Template metadata
applies_to: [MATH221, MATH251, STAT253]  # Or use [ALL]
defaults:
  weight: 2
  category: setup

# Task definitions
tasks:
  - key: UNIQUE-KEY
    id: "{{course.code}}-2025F-UNIQUE-KEY"
    title: "{{course.code}} — Task Title"
    description: "Detailed task description"
    category: setup|content|technical|materials|assessment|communication
    weight: 1-5
    due_offset: { days: -7, from: semester.first_day }
    blocked_by: ["DEPENDENCY-KEY"]
    parent_id: "{{course.code}}-2025F-PARENT-KEY"
```

### Field Descriptions

| Field | Required | Description |
|-------|----------|-------------|
| `key` | No | Short unique identifier for the task |
| `id` | No | Full task ID (auto-generated if not provided) |
| `title` | Yes | Task title with variable substitution |
| `description` | No | Detailed task description |
| `category` | No | Task category for filtering and prioritization |
| `weight` | No | Task importance/effort (1-5 scale) |
| `due_offset` | No | Due date calculation relative to anchor date |
| `blocked_by` | No | List of task dependencies |
| `parent_id` | No | Parent task for hierarchical organization |

## Variable Substitution

Templates support variable substitution using `{{variable}}` syntax:

### Available Variables

```yaml
# Course variables
{{course.code}}        # e.g., "MATH221"
{{course.name}}        # Full course name
{{course.section}}     # Section number
{{course.credits}}     # Credit hours
{{course.instructor}}  # Instructor name

# Semester variables
{{semester.first_day}} # Semester start date
{{semester.last_day}}  # Semester end date
{{semester.name}}      # e.g., "Fall 2025"
```

### Example Usage

```yaml
tasks:
  - title: "{{course.code}} — Generate syllabus for {{semester.name}}"
    description: "Create syllabus for {{course.name}} ({{course.credits}} credits)"
```

## Due Date Calculations

Due dates are calculated using offset specifications:

### Offset Structure

```yaml
due_offset:
  days: -7              # Number of days (negative = before)
  from: semester.first_day  # Anchor point
```

### Anchor Points

- `semester.first_day`: First day of classes
- `semester.last_day`: Last day of classes
- `today`: Current date (for dynamic deadlines)
- Any specific date: `"2025-08-18"`

### Examples

```yaml
# 7 days before semester starts
due_offset: { days: -7, from: semester.first_day }

# 30 days after semester starts
due_offset: { days: 30, from: semester.first_day }

# 14 days from today
due_offset: { days: 14, from: today }
```

## Dependency Management

### Simple Dependencies

```yaml
tasks:
  - key: TASK-A
    title: "First task"

  - key: TASK-B
    title: "Second task"
    blocked_by: ["TASK-A"]  # B depends on A
```

### Multiple Dependencies

```yaml
tasks:
  - key: FINAL-REVIEW
    title: "Final review"
    blocked_by:
      - "CONTENT-COMPLETE"
      - "ASSESSMENT-READY"
      - "LTI-CONFIGURED"
```

### Cross-Course Dependencies

Use full task IDs for cross-course dependencies:

```yaml
blocked_by:
  - "{{course.code}}-2025F-PREREQUISITE"
  - "MATH221-2025F-SHARED-RESOURCE"  # Specific course
```

## Hierarchical Tasks

Create parent-child relationships for task organization:

```yaml
tasks:
  # Parent task (rollup)
  - key: WEEK-01-ROLLUP
    id: "{{course.code}}-2025F-W01-ROLLUP"
    title: "Week 1 Complete"
    blocked_by:  # Blocked by all children
      - "{{course.code}}-2025F-W01-CONTENT"
      - "{{course.code}}-2025F-W01-ASSESSMENT"
      - "{{course.code}}-2025F-W01-ANNOUNCE"

  # Child tasks
  - key: W01-CONTENT
    id: "{{course.code}}-2025F-W01-CONTENT"
    title: "Week 1 Content"
    parent_id: "{{course.code}}-2025F-W01-ROLLUP"

  - key: W01-ASSESSMENT
    id: "{{course.code}}-2025F-W01-ASSESSMENT"
    title: "Week 1 Assessment"
    parent_id: "{{course.code}}-2025F-W01-ROLLUP"
```

## Multi-Document Templates

Templates can contain multiple YAML documents separated by `---`:

```yaml
# Core tasks for all courses
applies_to: [ALL]
tasks:
  - key: PREFLIGHT
    title: "Preflight checks"
---
# MATH221-specific tasks
applies_to: [MATH221]
tasks:
  - key: APPLIED-EXAMPLES
    title: "Add business examples"
---
# STAT253-specific tasks
applies_to: [STAT253]
tasks:
  - key: R-SETUP
    title: "Configure R environment"
```

## Template Files

### Organization

```
dashboard/tools/templates/
├── fall25_blackboard_ultra.yaml    # Main course setup tasks
├── fall25_weekly_static.yaml       # Weekly module tasks
└── fall25_course_specific.yaml     # Course-specific additions
```

### Loading Order

Templates are processed alphabetically, allowing for:

1. Base templates (prefixed with numbers: `01_base.yaml`)
2. Category templates (`02_content.yaml`, `03_assessment.yaml`)
3. Course-specific overrides (`99_math221_custom.yaml`)

## Task Categories

Standard categories with their typical use:

| Category | Purpose | Priority Phase |
|----------|---------|----------------|
| `setup` | Infrastructure, LMS configuration | Pre-launch |
| `content` | Learning materials, modules | Pre-launch |
| `technical` | Tools, integrations, LTI | Launch week |
| `materials` | Syllabi, resources, handouts | Pre-launch |
| `assessment` | Quizzes, tests, gradebook | Launch week |
| `communication` | Announcements, emails | Week one |

## Complete Example

### Course Setup Template

```yaml
# dashboard/tools/templates/course_setup.yaml
applies_to: [MATH221, MATH251, STAT253]

defaults:
  weight: 2
  category: setup

tasks:
  # Main setup task
  - key: COURSE-SETUP
    id: "{{course.code}}-2025F-SETUP"
    title: "{{course.code}} — Initial Course Setup"
    description: "Configure course shell in Blackboard"
    category: setup
    weight: 3
    due_offset: { days: -21, from: semester.first_day }

  # Dependent tasks
  - key: COPY-CONTENT
    id: "{{course.code}}-2025F-COPY"
    title: "{{course.code}} — Copy Prior Content"
    description: "Import content from previous semester"
    category: content
    weight: 3
    due_offset: { days: -20, from: semester.first_day }
    blocked_by: ["{{course.code}}-2025F-SETUP"]

  - key: UPDATE-DATES
    id: "{{course.code}}-2025F-DATES"
    title: "{{course.code}} — Update All Dates"
    description: "Batch update due dates for new semester"
    category: setup
    weight: 2
    due_offset: { days: -18, from: semester.first_day }
    blocked_by: ["{{course.code}}-2025F-COPY"]

  # Verification task
  - key: QA-CHECK
    id: "{{course.code}}-2025F-QA"
    title: "{{course.code}} — Quality Assurance"
    description: "Test all links, tools, and assessments"
    category: setup
    weight: 4
    due_offset: { days: -7, from: semester.first_day }
    blocked_by:
      - "{{course.code}}-2025F-DATES"
      - "{{course.code}}-2025F-SYLLABUS"
    checklist:
      - "Test all LTI tools"
      - "Verify gradebook calculations"
      - "Check assignment due dates"
      - "Test as student view"
```

## Generation Process

### Running the Generator

```bash
# Generate tasks from templates
python dashboard/tools/generate_tasks.py \
  --courses dashboard/state/courses.json \
  --templates dashboard/tools/templates \
  --out dashboard/state/tasks.json \
  --verbose
```

### Generator Workflow

1. **Load course data** from `courses.json`
2. **Process each template** file in order
3. **Apply templates** to specified courses
4. **Substitute variables** in task fields
5. **Calculate due dates** from offsets
6. **Convert blocked_by** to depends_on format
7. **Sort tasks** by due date and weight
8. **Write output** to tasks.json

## Best Practices

### 1. Use Meaningful Keys

```yaml
# Good: Descriptive and unique
- key: GRADEBOOK-CATEGORIES-SETUP
- key: WEEK-03-QUIZ-CONFIG

# Bad: Generic or ambiguous
- key: TASK-1
- key: SETUP
```

### 2. Group Related Tasks

Use parent tasks to group related work:

```yaml
- key: WEEK-01-PARENT
  blocked_by: [all-child-tasks]

- key: WEEK-01-CHILD-1
  parent_id: "{{course.code}}-WEEK-01-PARENT"
```

### 3. Set Appropriate Weights

- Weight 1: Quick, simple tasks (< 30 min)
- Weight 2: Standard tasks (30-60 min)
- Weight 3: Complex tasks (1-2 hours)
- Weight 4: Major tasks (2-4 hours)
- Weight 5: Critical multi-day tasks

### 4. Use Realistic Due Dates

```yaml
# Infrastructure: 3-4 weeks before
due_offset: { days: -21, from: semester.first_day }

# Content: 2-3 weeks before
due_offset: { days: -14, from: semester.first_day }

# Final checks: 1 week before
due_offset: { days: -7, from: semester.first_day }
```

### 5. Document Complex Dependencies

Add descriptions explaining why dependencies exist:

```yaml
- key: FINAL-EXAM
  description: "Configure final exam (requires pool and gradebook)"
  blocked_by:
    - "QUESTION-POOL"    # Need questions first
    - "GRADEBOOK-SETUP"  # Must have category
```

## Validation

### Check Template Syntax

```bash
# Validate YAML syntax
python -m yaml dashboard/tools/templates/*.yaml

# Validate generated tasks
python dashboard/tools/validate.py \
  --tasks dashboard/state/tasks.json
```

### Common Validation Errors

**Circular dependencies**

```
ERROR: Circular dependency detected: A → B → C → A
```

Solution: Review and break the cycle

**Missing dependencies**

```
WARNING: Task references unknown dependency: NONEXISTENT-TASK
```

Solution: Check task keys and IDs

**Invalid dates**

```
ERROR: Due date calculation failed for task X
```

Solution: Verify offset configuration

## Advanced Features

### Conditional Tasks

Use course properties for conditional generation:

```yaml
# In template
{% if course.online %}
- key: ONLINE-ORIENTATION
  title: "Online student orientation"
{% endif %}
```

### Dynamic Checklists

Generate checklists from course data:

```yaml
checklist:
  {% for week in course.weeks %}
  - "Review Week {{ week.number }} content"
  {% endfor %}
```

### Template Inheritance

Create base templates and extend them:

```yaml
# base_template.yaml
defaults: &base_defaults
  weight: 2
  category: setup

# extended_template.yaml
defaults:
  <<: *base_defaults
  weight: 3  # Override weight
```

## Troubleshooting

### Tasks Not Appearing

1. Check `applies_to` includes the course
2. Verify template file is in correct directory
3. Check for YAML syntax errors
4. Review generator output for warnings

### Dependencies Not Working

1. Ensure task IDs match exactly
2. Check for typos in `blocked_by` lists
3. Verify referenced tasks exist
4. Use full IDs for cross-course deps

### Due Dates Incorrect

1. Verify semester dates in courses.json
2. Check offset calculations (negative = before)
3. Ensure anchor dates are valid
4. Test with different `from` values

## Support

For template issues:

- Check YAML syntax with online validators
- Review generated tasks.json for output
- Enable verbose mode in generator
- Consult template examples in docs/examples/
