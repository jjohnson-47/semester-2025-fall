# Architecture Overview

- V2 projection system: normalize once, render many
- Rules Engine: centralized business logic (no-weekend, holidays)
- Dashboard: Flask app with SQLite repo (DB-first), HTMX endpoints
- Build Pipeline: scripts/build_pipeline.py (staged, idempotent)

## Data flows
- content/courses/* → CourseService → Rules → Projections → Builders → build/
- Dashboard API → DB repo → dependency service → HTMX views

