# 🚀 Quick Reference - Semester Management System

## Most Common Commands

### Daily Operations

```bash
make validate          # Validate all JSON files
make syllabi          # Generate all syllabi
make schedules        # Generate all schedules
make all              # Complete build
make serve-site       # Local preview at :8000
```

### Course-Specific

```bash
make course COURSE=MATH221   # Build single course
make course COURSE=MATH251
make course COURSE=STAT253
```

### Deployment

```bash
make build-site ENV=preview   # Build for preview
make build-site ENV=prod      # Build for production
# Then GitHub Actions handles deployment
```

## File Locations

### Source Data (Edit These)

```
content/courses/MATH221/*.json   # MATH221 data
content/courses/MATH251/*.json   # MATH251 data
content/courses/STAT253/*.json   # STAT253 data
variables/semester.json          # Master calendar
profiles/instructor.json         # Your info
```

### Generated Files (Don't Edit)

```
build/syllabi/           # Generated syllabi
build/schedules/         # Generated schedules
build/packages/          # Blackboard packages
site/                    # Deployment files
```

## Key JSON Files Per Course

Each course has:

- `course_info.json` - Basic info (CRN, section, format)
- `schedule.json` - Weekly topics and assignments
- `due_dates.json` - Platform-specific deadlines
- `grading.json` - Grade weights and scale
- `textbook.json` - Required materials
- `rsi.json` - Regular interaction text
- `policies.json` - Course policies
- `technology.json` - Platform requirements

## Platform Details

### MATH221 - MyOpenMath

- Course ID: 292612
- Enrollment Key: math221fall2025
- Due dates: Fridays

### MATH251 - Edfinity

- Course: Calculus 1 - Fall 2025
- Complex schedule with quizzes
- Written Problems: Mondays

### STAT253 - Pearson MyLab

- Course ID: johnson86763
- Integrated with Blackboard Ultra
- Includes R assignments

## Important Dates

- **Semester**: Aug 25 - Dec 13, 2025
- **Add/Drop**: Sep 5, 2025
- **Withdrawal**: Oct 31, 2025
- **Labor Day**: Sep 1 (no classes)
- **Fall Break**: Nov 27-28
- **Finals**: Dec 8-13

## Validation Errors?

```bash
# Check specific file
cat content/courses/MATH221/schedule.json | jq .

# Validate single course
uv run python scripts/validate.py MATH221

# Clean rebuild
rm -rf build/ site/
make clean
make all
```

## Git Workflow

```bash
# Check status
git status

# Stage changes
git add -A

# Commit (I'll handle this for you)
# Just ask: "commit changes"

# Push to GitHub
git push origin main
```

## Emergency Fixes

### Duplicate Year in Syllabus

Edit `.env`: `SEMESTER_NAME="Fall"`

### JSON Validation Failed

Check for:

- Missing commas
- Extra commas at end
- Mismatched brackets
- Invalid dates

### Deployment Failed

1. Check GitHub Actions tab
2. Verify secrets are set
3. Try manual workflow dispatch

## Agent Commands

Quick ways to use agents:

```bash
# Validate everything
"Run full validation"

# Update specific course
"Rebuild MATH221 syllabus"

# Deploy
"Deploy to preview"
"Deploy to production"

# Fix dates
"Update all due dates for Labor Day"
```

## URLs

- **Production**: <https://production.jeffsthings-courses.pages.dev/>
- **Preview**: https://[hash].jeffsthings-courses.pages.dev/
- **GitHub**: Your repository
- **Manifest**: /manifest.json

## Need Help?

1. Check `docs/` folder
2. Read AGENTS.md
3. Check GitHub Actions logs
4. Ask: "What's wrong with [specific issue]?"

---
*Last Updated: August 24, 2025 | Fall 2025 Semester*
