# Build Process Documentation

## Overview

This project uses a clear, sequential build process to generate course syllabi and schedules, then deploy them to a public site. Understanding this flow prevents confusion and ensures consistency.

## Build Flow

```
JSON Data → Internal Build → Public Site → Content Delivery
```

### 1. Content Sources (`content/courses/`)
- **Location**: `content/courses/{COURSE}/`
- **Files**: `rsi.json`, `schedule.json`, `evaluation_tools.json`, etc.
- **Purpose**: Single source of truth for all course content

### 2. Internal Build (`build/`)
- **Command**: `python scripts/build_syllabi.py`
- **Output**: `build/syllabi/{COURSE}.html`, `build/schedules/{COURSE}.html`
- **Purpose**: High-quality, complete documents for internal use and as source for public site

### 3. Public Site Generation (`site/`)
- **Command**: `python scripts/site_build.py --include syllabus schedule`
- **Source**: Uses HTML from `build/` directory (NOT regenerating from JSON)
- **Output**: `site/courses/{COURSE}/fall-2025/syllabus/index.html`
- **Purpose**: Production-ready pages with proper URLs and iframe embeds

### 4. Content Delivery (External)
- **System**: `jeffsthings-courses` repository 
- **URL**: `https://courses.jeffsthings.com/`
- **Sync**: Manual via `pnpm sync` and `pnpm deploy` in external repo

## Key Commands

### Full Build Sequence
```bash
# 1. Build internal syllabi and schedules
python scripts/build_syllabi.py
python scripts/build_schedules.py

# 2. Generate public site
python scripts/site_build.py --include syllabus schedule

# 3. Content delivery (in jeffsthings-courses repo)
pnpm sync
pnpm deploy
```

### Development/Testing
```bash
# Build specific course
python scripts/build_syllabi.py --course MATH221

# Local site preview
python -m http.server 8000 -d site/
```

### Dashboard Integration
```bash
# Start Flask dashboard
cd dashboard && python app.py

# Dashboard previews use Blackboard-optimized content from site/
# Automatically starts local site server if needed (http://localhost:8000)
# All previews now match production content exactly
```

### Dashboard Features
- **Syllabus Preview**: Shows exact Blackboard-optimized content 
- **Schedule Preview**: Uses production embed versions
- **iframe Generator**: Links to production URL (courses.jeffsthings.com/embed/generator/)
- **Auto Site Server**: Dashboard automatically starts local site preview when needed
- **Production Parity**: What you see in dashboard = what goes to Blackboard

## Important Notes

### RSI Content Mapping
- **Source**: `content/courses/{COURSE}/rsi.json` → `course_policies.interaction`
- **Template**: Expects `rsi.text` 
- **Mapping**: Build process transforms `course_policies.interaction` → `rsi.text`

### Default Build Exclusions
- `site_build.py` by default excludes `syllabus` and `schedule`
- Must use `--include syllabus schedule` to build these pages
- This prevents accidental overwrites during development

### File Dependencies
1. **JSON → HTML**: `build_syllabi.py` processes JSON into HTML
2. **HTML → Site**: `site_build.py` copies and adapts HTML from `build/`
3. **Never**: `site_build.py` should NOT regenerate from JSON directly

## Troubleshooting

### Missing RSI Content
```bash
# Check source data
cat content/courses/MATH221/rsi.json | jq '.course_policies.interaction'

# Rebuild syllabi 
python scripts/build_syllabi.py

# Check build output
grep -A 2 "Regular and Substantive Interaction" build/syllabi/MATH221.html

# Rebuild site
python scripts/site_build.py --include syllabus
```

### Empty or Outdated Site Content
```bash
# Clean rebuild
rm -rf site/ build/
python scripts/build_syllabi.py
python scripts/build_schedules.py
python scripts/site_build.py --include syllabus schedule
```

### Dashboard Shows Different Content
- Dashboard previews use `site/` content  
- If dashboard differs from expectations, rebuild site
- Dashboard iframe URLs point to production domain for Blackboard embedding

## Architecture Principles

1. **Single Source of Truth**: All content originates from JSON files in `content/`
2. **Build Pipeline**: JSON → `build/` → `site/` → production
3. **No Regeneration**: `site_build.py` reuses `build/` artifacts, never regenerates from JSON
4. **Template Consistency**: Same templates used for both `build/` and dashboard preview
5. **Production Parity**: Dashboard preview shows actual production content