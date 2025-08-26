# Repository Architecture and Project Structure (Fall 2025)

This report documents the full architecture, data flow, and build/deployment structure of the Fall 2025 semester project. It is written independently and does not rely on any other architecture report in this repository.

## 1) Executive Summary

- Purpose: A “content factory” that turns structured JSON + Jinja2 templates into high‑quality syllabi, schedules, and Blackboard packages, with a Flask dashboard for orchestration and a static site for public delivery/iframe embedding.
- Single source of truth: `academic-calendar.json`, `variables/semester.json`, `profiles/instructor.json`, and `content/courses/*/*.json` drive all generated artifacts.
- Build system: `make` targets orchestrate validation → calendar → syllabi → schedules → weekly pages → Blackboard packages, plus site builds for Cloudflare Pages.
- Runtime: A Flask dashboard in `dashboard/` manages task workflows, smart prioritization, and previews generated outputs.
- Deployment: `scripts/site_build.py` emits `site/` with Cloudflare headers/redirects and a manifest; Cloudflare Pages serves stable full/embed URLs for LMS iframes.

## 2) Repository Map (Responsibilities)

- `Makefile`: Primary build and dev entrypoints (validation, content generation, dashboard, tests, Cloudflare site build, CI helpers).
- `academic-calendar.json`: Master semester dates, holidays, and critical deadlines used by calendar- and schedule-related logic.
- `content/`
  - `courses/{MATH221|MATH251|STAT253}/*.json`: Per-course inputs (description, prerequisites, goals, schedule, due_dates overrides, RSI, etc.).
- `variables/semester.json`: Global semester settings injected into templates and builders.
- `profiles/instructor.json`: Instructor contact/profile used in templating and schedules.
- `templates/`: Jinja2 templates for syllabi and schedule HTML/Markdown; `templates/site/` for public site pages and embed generator.
- `scripts/`: Build pipeline scripts and shared utilities.
  - `build_syllabi.py`: SyllabusBuilder, renders HTML/MD (+ optional PDF) and calendar-appendix variants.
  - `build_schedules.py`: ScheduleBuilder, aligns course plans to calendar; generates MD and HTML.
  - `build_bb_packages.py`: Assembles Blackboard Ultra ZIP packages from generated artifacts.
  - `site_build.py`: Public site builder (full + embed variants, manifest, CF headers/redirects, assets).
  - `utils/semester_calendar.py`: Calendar service (weeks, holidays, ICS, finals detection).
  - `utils/jinja_env.py`: Jinja environment + custom filters (markdown, dates, ordinals, etc.).
  - `validate_json.py`: JSON schema validation across configured directories.
- `dashboard/`: Flask app for task orchestration and status views.
  - `app.py`: Routes, lightweight JSON API, task persistence with file locking.
  - `config.py`: Config classes (development/testing/production), env integration, paths.
  - `orchestrator.py`: Agent‑style orchestrator with dependency analysis, critical path, learning metrics.
  - `tools/`: Task generation, validation, reprioritization (contracts), exports, resets.
  - `templates/`: Dashboard UI (base, kanban, tasks, previews).
  - `state/`: Generated dashboard state (courses/tasks JSON, now‑queue, etc.).
- `assets/`: CSS/JS for public site and course‑specific styling; copied into `site/` during site build.
- `cloudflare/`: `_headers.*`, `_redirects`, and `functions/` copied into `site/` for deployment behavior.
- `tests/`: Pytest suite for dashboard, tools, schedule alignment, JSON validation, and services.
- `pyproject.toml`: Dependencies, optional extras, linters/formatters, mypy/pytest/coverage configuration.

## 3) Data Model and Sources

- Course data (per course):
  - `course_meta.json`: section/format/credits/CRN, etc.; env vars can fill gaps for titles/meeting info.
  - `schedule.json`: planned weekly topics/readings/assignments/assessments.
  - `due_dates.json`: optional precise due‑date overrides (platform‑specific exports), used before heuristics.
  - Additional policy/description JSON: grading, goals, outcomes, prerequisites, RSI, etc.
- Global data:
  - `academic-calendar.json`: authoritative semester timeline (start/end, finals, holidays, critical deadlines).
  - `variables/*.json`: semester‑level configuration injected with `var_<name>` keys.
  - `profiles/instructor.json`: instructor details used in syllabi/schedules.

All JSON is validated by `scripts/validate_json.py` against schemas in `scripts/utils/schema/` where present. The validator reports per‑directory results and a summary with error/warning counts; `make validate` runs it as a standard pre‑build gate.

## 4) Template and Rendering Layer

- Jinja environment: `scripts/utils/jinja_env.py`
  - Filters: `markdown`, `date`, `ordinal`, `percentage`, `phone`, `titlecase`, `weekday`.
  - Globals: `now`, `today` and helper globals for formatting codes/credits/sections.
- Syllabi templates: `templates/syllabus.html.j2`, `templates/syllabus.md.j2` with optional schedule appendix injection.
- Schedule template: `templates/course_schedule.html.j2` for HTML; MD table emitted by builder.
- Site templates: `templates/site/*.j2` including an iframe embed generator used in the public site.

## 5) Core Services and Builders

### Semester Calendar Service (`scripts/utils/semester_calendar.py`)
- Loads `academic-calendar.json` (with fallbacks) and exposes:
  - `get_semester_dates()`: start/end, finals, add/drop, withdrawal.
  - `get_holidays()`: normalized entries spanning single‑day and ranged holidays.
  - `get_weeks()`: Mon–Fri buckets, annotating holidays and finals week.
  - `generate_ics(course)`: ICS feed with key milestones and holidays.

### Schedule Builder (`scripts/build_schedules.py`)
- Inputs: calendar service + `content/courses/<C>/schedule.json` (optional) + `due_dates.json` (optional overrides).
- Outputs: `build/schedules/<C>_schedule.md` and `..._schedule.html`.
- Heuristics:
  - Assignments: default due on Fri; discussions/BB items Wed; quizzes Fri; exams Thu; never weekends.
  - Holiday shifts (e.g., Fall Break) to keep assessments on Wed of same week or push HW to next Mon.
  - Custom due dates override all heuristics when provided.

### Syllabus Builder (`scripts/build_syllabi.py`)
- Inputs: per‑course JSON, global variables, instructor, and course calendar snapshot.
- Outputs: `build/syllabi/<C>.html`, `<C>.md`, and variants with calendar appendix (`*_with_calendar.*`). Optional PDF via WeasyPrint or Pandoc when available.
- Ensures schedule is generated and embeds schedule content in appendix variants.

### Blackboard Packages (`scripts/build_bb_packages.py`)
- Assembles ZIP packages per course in `build/blackboard/` including syllabus, schedule MD, and a `start_here.html`, with a simple `manifest.json`.

## 6) Build Orchestration (Makefile)

- Validation and initialization:
  - `make init`: sync deps via `uv`; runs `make validate`.
  - `make validate`: JSON schema validation.
- Content pipeline:
  - `make calendar` → `make syllabi` → `make schedules` → `make weekly` → `make packages`.
  - `make course COURSE=CODE`: targeted build for a single course.
- Lint/format/tests:
  - `make lint` (ruff + mypy), `make format` (ruff format + fixes), `make test` (pytest with coverage).
- Dashboard workflow:
  - `make dash-init` → `dash-gen` (task gen) → `dash-validate` (integrity) → `dash` (run Flask on 127.0.0.1:5055), plus helpers (`dash-prioritize`, `dash-export`, `dash-snapshot`, `dash-reset`).
- Public site:
  - `make build-site`: builds `site/` with per‑course full/embed pages and `manifest.json`; copies Cloudflare `_headers`/`_redirects`.
  - `make serve-site`: simple local static server; `make compare-site`: compare legacy `build/` vs new `site/`.
  - Cloudflare Pages ops via cf‑go: `pages-*` and DNS helpers (require gopass‑provided credentials).

## 7) Dashboard Architecture (`dashboard/`)

- App structure:
  - `app.py`: Flask app with routes (dashboard views, lightweight JSON API, exports), file‑locked JSON persistence under `dashboard/state/`, and helper functions for colors/priority/due states and relative time.
  - `config.py`: Dev/Test/Prod config classes; resolves paths for build outputs and content sources; loads `.env` and optional `.env.secrets`.
  - `orchestrator.py`: Task graph analysis (cycles, parallel groups, critical path), learning from execution metrics, and agent coordination to suggest/assign work.
  - `tools/`: YAML‑driven task generation, validation, reprioritization with contracts, and export/reset utilities.
  - `templates/`: Bootstrap UI for kanban, lists, syllabus preview, and filtered views.
- State model:
  - `dashboard/state/tasks.json` and `courses.json` are the mutable data stores; optional `now_queue.json` for focus.
  - Git snapshotting available for state changes (configurable with `AUTO_SNAPSHOT`).

## 8) Public Site Builder (`scripts/site_build.py` → `site/`)

- Purpose: Curated, student‑facing site with stable per‑course URLs and embed variants for LMS iframes.
- Inputs: existing high‑quality HTML from `build/syllabi/*.html` and `build/schedules/*_schedule.html`, plus assets.
- Outputs:
  - `site/courses/<COURSE>/<term>/syllabus/` and `/schedule/` with `index.html`.
  - Matching `.../embed/` pages optimized for iframes (injects minimal styles).
  - `site/manifest.json` enumerating available docs per course and whether custom due dates exist.
  - Cloudflare config copied: `_headers` and `_redirects` for headers and routing; `functions/` if present.
  - `site/assets/` populated with CSS/JS, preferring layered `assets/` and falling back to legacy `build/css/*` if needed.

## 9) Configuration, Environment, and Secrets

- Python toolchain via `uv`; dependencies (Jinja2, Flask, jsonschema, markdown, pytz, dateutil) in `pyproject.toml`.
- Environment variables: `.env` loaded opportunistically by builders and dashboard config; `.env.example` shows safe defaults.
- Cloudflare: `.cloudflare` and `wrangler.jsonc` hold project context; credentials are loaded from gopass at runtime in `make pages-*` targets.
- Security posture: no secrets in VCS; least‑privilege assumptions in Make targets; CORS restricted in production config; HTTPS/cookie flags tightened in `ProductionConfig`.

## 10) Testing and Quality Gates

- Tests: `tests/` includes unit/integration coverage for dashboard endpoints, tools, schedule alignment, JSON validation, orchestration helpers, and view logic.
- Pytest configuration: strict warnings; coverage targets for `dashboard` and `scripts` with branch coverage and HTML/XML reports (`pyproject.toml`).
- Linting/formatting: Ruff (lint + format), mypy strictness, and Black config; pre‑commit hooks available.
- CI recipes: `ci-*` make targets for validate/build/test/lint; dev setup via `make dev-setup`.

## 11) End‑to‑End Data Flow

1) Author updates JSON sources under `content/`, `variables/`, `profiles/`, and semester calendar.
2) `make validate` checks schema compliance and basic integrity.
3) `make calendar` produces week structures/ICS for use by builders.
4) `make syllabi` uses Jinja templates to render HTML/MD (+ appendices) per course; optional PDF.
5) `make schedules` emits per‑course schedule MD + HTML, applying holiday rules and custom overrides.
6) `make weekly` builds weekly overviews for legacy/auxiliary outputs.
7) `make packages` assembles Blackboard ZIPs including syllabus/schedule and a “Start Here”.
8) `make build-site` copies curated HTML into stable, per‑course full/embed URLs, attaches assets and CF config, and writes `manifest.json`.
9) Dashboard (`make dash`) provides visibility, prioritization, and orchestration for the overall process.

## 12) Notable Design Choices

- Separation of concerns:
  - Builders generate canonical HTML/MD into `build/` for internal use and artifacts.
  - Public site copies and adapts those artifacts into `site/` with a minimal adaptation layer (embed styles, assets, headers) suitable for production hosting.
- Holiday‑aware schedule logic prevents weekend due dates and respects major breaks without sacrificing clarity.
- Graceful degradation:
  - Builders tolerate missing optional deps (PDF tools), absent templates, or incomplete course data, logging warnings and emitting placeholders when necessary.
- Testable architecture:
  - Builders/services designed for injection (e.g., calendar instance), allowing targeted tests around date logic and formatting.

## 13) How to Navigate and Extend

- Add a course: scaffold JSON under `content/courses/<CODE>/`, then run `make validate && make all`.
- Adjust schedule heuristics: edit `ScheduleBuilder` methods for weekday selection/holiday shift.
- Update templates: change `templates/*.j2` (syllabus/schedule/site) and re‑run builds.
- Add global policies: place JSON in `global/` or extend `variables/` and consume via template context.
- Expand dashboard: add routes/views in `dashboard/`, new task templates in `dashboard/tools/templates`, or enrich prioritization contracts.
- Deploy: use `make build-site` and Cloudflare commands; exported site is entirely static with headers/redirects set by `_headers.*` and `_redirects`.

---

This overview reflects the current repository as of Fall 2025, detailing how inputs flow through validation and templating into reproducible, deployable artifacts, while the dashboard and site builder provide operational visibility and distribution.

