# V2 Architecture Archive Guide

> **Deployment guidance retired on 2026-07-14.** This guide now documents how
> to reproduce and inspect the Fall 2025 V2 output locally. The published site
> is retained as a public archive, but automatic and dashboard-driven
> publication are retired. Reactivation requires a new owner decision under
> [`adr/0005-retained-public-archive.md`](adr/0005-retained-public-archive.md).

## Architecture Summary

The V2 content factory in this repository transforms the JSON course sources
into purpose-specific projections, renders HTML with embedded styles, and
enforces course rules such as avoiding weekend due dates. Its local outputs are
the ignored `build/` tree and the retained static `site/` tree.

The public archive may continue to be served at:

- <https://courses.jeffsthings.com/>
- <https://production.jeffsthings-courses.pages.dev/>

Those URLs describe retained delivery surfaces. A repository push does not
publish a new build.

## Supported V2 Build Process

Always use `BUILD_MODE=v2` and UV-backed repository commands:

```bash
# Validate source data first
BUILD_MODE=v2 make validate

# Build all local course output
BUILD_MODE=v2 make all

# Build individual components
BUILD_MODE=v2 make syllabi
BUILD_MODE=v2 make schedules

# Rebuild retained static archive output locally
BUILD_MODE=v2 make build-site ENV=preview
```

### Key Components

1. **Projection System** (`scripts/services/projection_adapter.py`)
   - Transforms JSON data into view-specific projections.
   - Applies centralized business rules.
   - Preserves consistent rendering inputs.

2. **Style System** (`scripts/utils/style_system.py`)
   - Embeds CSS for standalone and LMS-compatible viewing.
   - Applies course-specific themes.

3. **Template System** (`templates/`)
   - Uses Jinja2 templates and V2 projection data.
   - Separates source content from presentation.

4. **Site Builder** (`scripts/site_build.py`)
   - Generates a deliberately limited public tree.
   - Uses explicit include/exclude controls for course documents.
   - Writes the archive manifest and security headers.

## Local Verification

Run validation before generation, then verify the expected archive files:

```bash
BUILD_MODE=v2 make validate
BUILD_MODE=v2 make test
BUILD_MODE=v2 make build-site ENV=preview
test -f site/manifest.json
test -f site/_headers
```

For an isolated preview that does not publish anything:

```bash
BUILD_MODE=v2 make serve-site
```

The current archive build keeps its public-data boundary: dashboard routes,
task state, administrative APIs, credentials, and student private information
must not enter `site/`.

## Historical Publication Design

During the Fall 2025 semester, this document described three publication paths:
a dashboard one-click action, a command-line push, and a GitHub Actions job.
The intended pipeline built the V2 site, uploaded it to Cloudflare Pages, and
verified URLs and iframe headers. The repository also carried deployment API
and orchestration-state tests for that operating period.

Those publication paths are no longer active:

- the Pages pull-request/main workflow is removed;
- the dashboard deployment API and client control are removed;
- scheduled semester maintenance is removed; and
- historical orchestration-state tests are removed.

The V2 projection, rules, templates, local builder, static archive, and isolated
tests remain. Historical reports may still name the retired surfaces; they are
evidence of completed work, not current operating authority.

## Troubleshooting Local Builds

1. Confirm `BUILD_MODE=v2` is set for repository commands.
2. Run `BUILD_MODE=v2 make validate` before generation.
3. Use `BUILD_MODE=v2 make clean` to clear generated local artifacts when a
   rebuild is necessary.
4. Run Python entry points with `uv run`, never bare `python`, `pip`, or a
   hand-managed virtual environment.
5. Treat a green local build as reproducibility evidence only, not deployment
   evidence.

## Reactivation

Do not create, retrieve, rotate, or install deployment credentials for routine
archive maintenance. Do not re-add a push- or pull-request-triggered deployment
workflow. Publication may be re-enabled only through a new owner decision and
the complete reactivation gate in ADR 0005.

The dedicated historical Cloudflare record is in
[`CLOUDFLARE_DEPLOYMENT.md`](CLOUDFLARE_DEPLOYMENT.md), and current local builder
details are in [`SITE_BUILDER.md`](SITE_BUILDER.md).
