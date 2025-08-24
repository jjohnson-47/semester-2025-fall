# Cloudflare Pages Implementation Guide

## Course Content System with Private Dashboard & Blackboard Integration

---

## 1. Architecture Overview

### Core Principles

- **Single source of truth**: Shared content lives once in `content/global`; courses only override when necessary
- **Layered variables**: `variables/static` < `variables/annual.2025` < `variables/semester.fall-2025` < `course overrides`
- **Parallel operation**: Keep current `build/` pipeline; add `site/` for Pages during transition
- **Stable URLs**: `/courses/<COURSE>/<term>/<doc>/` plus `/courses/<COURSE>/latest/` (redirect)
- **Zero duplication**: Enforce with hashing + include-only templates
- **Privacy boundaries**: Dashboard stays private (local-only); public site hosts only student-facing content

### Deployment Model

- **Public Site** (Cloudflare Pages): Static course content, embed pages, minimal edge functions
- **Private Dashboard** (Flask @ :5055): Local development only, includes Preview Hub for testing
- **Blackboard Integration**: Iframe-ready pages with no navigation, environment-aware CSP

---

## 2. Repository Structure

```
semester-2025-fall/
├─ content/
│  ├─ courses/
│  │  ├─ MATH221/
│  │  │  ├─ data/
│  │  │  ├─ assets/
│  │  │  └─ overrides/             # course-specific diffs
│  │  ├─ MATH251/
│  │  └─ STAT253/
│  └─ global/
│     ├─ policies/
│     ├─ snippets/
│     └─ people/
│
├─ templates/
│  ├─ syllabus.html.j2
│  ├─ schedule.html.j2
│  └─ partials/
│
├─ variables/
│  ├─ static.json
│  ├─ annual.2025.json
│  └─ semester.fall-2025.json
│
├─ dashboard/                      # PRIVATE - not deployed
│  ├─ app.py
│  ├─ templates/
│  │  └─ preview/                 # Preview Hub templates
│  ├─ state/
│  └─ tools/
│
├─ scripts/
│  ├─ build.py                    # renders to site/, generates manifest.json
│  ├─ validate.py
│  ├─ check_dedupe.py
│  ├─ export_blackboard.py        # emits iframe snippets
│  └─ priority.py
│
├─ build/                         # legacy output (keep for comparison)
├─ site/                          # Pages-ready static output
├─ schema/
├─ cloudflare/
│  ├─ _headers.prod               # Production CSP (Blackboard only)
│  ├─ _headers.preview            # Preview CSP (Blackboard + localhost:5055)
│  ├─ _redirects
│  └─ functions/                  # Optional Pages Functions
│      └─ _embed/[...path].ts    # Dynamic nav stripping if needed
├─ pyproject.toml
├─ Makefile
└─ README.md
```

---

## 3. Security Headers & CSP Configuration

### Two-Profile System

**Production (_headers.prod)**

```
/*
  Content-Security-Policy: default-src 'self'; script-src 'self' https://www.desmos.com https://*.geogebra.org; style-src 'self' 'unsafe-inline'; img-src 'self' data: https://*.geogebra.org; frame-src 'self' https://www.desmos.com https://*.geogebra.org; frame-ancestors https://<blackboard-domain>;
  Referrer-Policy: no-referrer
  X-Content-Type-Options: nosniff
  Permissions-Policy: camera=(), microphone=(), geolocation=()

/assets/*
  Cache-Control: public, max-age=31536000, immutable

/*.html
  Cache-Control: no-cache
```

**Preview (_headers.preview)**

```
/*
  Content-Security-Policy: default-src 'self'; script-src 'self' https://www.desmos.com https://*.geogebra.org; style-src 'self' 'unsafe-inline'; img-src 'self' data: https://*.geogebra.org; frame-src 'self' https://www.desmos.com https://*.geogebra.org; frame-ancestors http://localhost:5055 https://<blackboard-domain>;
  Referrer-Policy: no-referrer
  X-Content-Type-Options: nosniff
  Permissions-Policy: camera=(), microphone=(), geolocation=()

/assets/*
  Cache-Control: public, max-age=31536000, immutable

/*.html
  Cache-Control: no-cache
```

### Key Differences

- **Production**: Only allows framing from Blackboard domain
- **Preview**: Allows framing from Blackboard AND local dashboard (localhost:5055)

---

## 4. Build System

### Makefile Targets

```make
PYTHON := uv run python
ENV ?= preview  # or prod
CF_PROJECT := your-project-name

.PHONY: validate dedupe build-site preview compare deploy-prod deploy-preview

validate:
 $(PYTHON) scripts/validate.py

dedupe:
 $(PYTHON) scripts/check_dedupe.py

build-site: validate dedupe
 $(PYTHON) scripts/build.py --out site/
 # Copy environment-specific headers
 cp cloudflare/_headers.$(ENV) site/_headers
 cp cloudflare/_redirects site/ 2>/dev/null || true
 # Copy functions if present
 [ -d cloudflare/functions ] && cp -R cloudflare/functions site/ || true

preview: build-site
 python -m http.server -d site 8000

compare:
 diff -qr build site || true

deploy-prod:
 $(MAKE) build-site ENV=prod
 wrangler pages deploy site --project-name $(CF_PROJECT) --branch production

deploy-preview:
 $(MAKE) build-site ENV=preview
 wrangler pages deploy site --project-name $(CF_PROJECT) --branch preview-$(shell date +%s)

dashboard:
 cd dashboard && $(PYTHON) app.py
```

### Build Script Requirements (scripts/build.py)

1. Generate both full and embed versions of each page
2. Create `site/manifest.json` for dashboard integration:

```json
{
  "MATH221": {
    "syllabus": {
      "prod_embed": "https://yourdomain.edu/courses/MATH221/fall-2025/syllabus/embed/",
      "preview_embed": "https://yourproject.pages.dev/courses/MATH221/fall-2025/syllabus/embed/",
      "prod_full": "https://yourdomain.edu/courses/MATH221/fall-2025/syllabus/",
      "preview_full": "https://yourproject.pages.dev/courses/MATH221/fall-2025/syllabus/"
    },
    "schedule": { ... }
  }
}
```

---

## 5. Embed Mode Implementation

### Static Approach (Recommended)

Build two variants of each page:

```
/courses/MATH221/fall-2025/syllabus/        # full navigation
/courses/MATH221/fall-2025/syllabus/embed/  # no navigation
```

Template logic (Jinja2):

```jinja2
{% if not EMBED_MODE %}
  <header>...</header>
  <nav>...</nav>
  <div class="breadcrumbs">...</div>
{% endif %}

<main class="{% if EMBED_MODE %}embed-content{% else %}full-content{% endif %}">
  {{ content }}
</main>

{% if not EMBED_MODE %}
  <footer>...</footer>
{% endif %}
```

### Dynamic Approach (Optional Fallback)

Pages Function at `cloudflare/functions/_embed/[...path].ts`:

```typescript
export const onRequest: PagesFunction = async (ctx) => {
  const url = new URL(ctx.request.url);
  const target = new URL(url.pathname.replace(/^\/_embed/, ""), url.origin);
  const resp = await fetch(target.toString(), ctx.request);

  const rewriter = new HTMLRewriter()
    .on("header, nav, .site-nav, .breadcrumbs, footer", {
      element(el) { el.remove(); }
    });

  const transformed = rewriter.transform(resp);

  // Determine environment from hostname
  const isPreview = url.hostname.includes('pages.dev');
  const frameAncestors = isPreview
    ? "https://<blackboard-domain> http://localhost:5055"
    : "https://<blackboard-domain>";

  return new Response(transformed.body, {
    headers: {
      "Content-Type": "text/html; charset=utf-8",
      "Content-Security-Policy": `default-src 'self'; script-src 'self' https://www.desmos.com https://*.geogebra.org; style-src 'self' 'unsafe-inline'; img-src 'self' data: https://*.geogebra.org; frame-src 'self' https://www.desmos.com https://*.geogebra.org; frame-ancestors ${frameAncestors}`,
      "X-Content-Type-Options": "nosniff"
    }
  });
};
```

---

## 6. Dashboard Preview Hub (Private, Local-Only)

### Key Features

- Course/document picker with dropdown navigation
- Environment toggle (Preview vs Production)
- Viewport presets (768/1024/1280px width)
- Copy helpers for Blackboard integration
- Status badges (validation, dedupe, linkcheck)
- Simulated Blackboard wrapper for context testing

### Implementation (dashboard/app.py)

```python
from flask import Flask, render_template, request
import json
from pathlib import Path

app = Flask(__name__)

@app.get("/preview")
def preview_index():
    """Preview hub homepage - lists all courses and docs"""
    manifest = json.load(open("../site/manifest.json"))
    return render_template("preview/index.html", manifest=manifest)

@app.get("/preview/<course>/<doc>")
def preview_page(course, doc):
    """Preview specific page in iframe"""
    manifest = json.load(open("../site/manifest.json"))
    env = request.args.get("env", "preview")  # preview | prod
    width = request.args.get("w", "1024")
    height = request.args.get("h", "1200")

    if env == "preview":
        url = manifest[course][doc]["preview_embed"]
    else:
        url = manifest[course][doc]["prod_embed"]

    return render_template("preview/iframe.html",
                           url=url,
                           course=course,
                           doc=doc,
                           width=width,
                           height=height,
                           env=env)

@app.get("/preview/snippet/<course>/<doc>")
def get_snippet(course, doc):
    """Generate Blackboard-ready iframe HTML"""
    manifest = json.load(open("../site/manifest.json"))
    url = manifest[course][doc]["prod_embed"]

    snippet = f'''<div style="max-width:1000px;margin:0 auto">
  <iframe src="{url}"
          width="100%" height="1200"
          style="border:0;overflow:auto"
          loading="lazy"
          referrerpolicy="no-referrer"
          allowfullscreen>
  </iframe>
</div>
<p>If the embed does not load,
   <a href="{url}" target="_blank">open in a new tab</a>.
</p>'''

    return {"snippet": snippet}

if __name__ == "__main__":
    app.run(port=5055, debug=True)
```

---

## 7. URL Structure & Redirects

### URL Contract

```
/courses/<COURSE>/<term>/syllabus/        → full page
/courses/<COURSE>/<term>/syllabus/embed/  → embed version
/courses/<COURSE>/<term>/schedule/        → full page
/courses/<COURSE>/<term>/schedule/embed/  → embed version
/courses/<COURSE>/latest/                 → 301 to current term
```

### Redirects (_redirects)

```
/courses/MATH221/latest/*  /courses/MATH221/fall-2025/:splat  301
/courses/MATH251/latest/*  /courses/MATH251/fall-2025/:splat  301
/courses/STAT253/latest/*  /courses/STAT253/fall-2025/:splat  301
```

---

## 8. CI/CD Pipeline

### GitHub Actions Workflow

```yaml
name: Build and Deploy

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: astral-sh/setup-uv@v3
      - run: make validate dedupe

  deploy:
    needs: validate
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: astral-sh/setup-uv@v3

      - name: Build Site
        run: |
          if [[ "${{ github.ref }}" == "refs/heads/main" ]]; then
            make build-site ENV=prod
          else
            make build-site ENV=preview
          fi

      - name: Deploy to Cloudflare Pages
        env:
          CLOUDFLARE_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          CLOUDFLARE_ACCOUNT_ID: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
        run: |
          if [[ "${{ github.ref }}" == "refs/heads/main" ]]; then
            wrangler pages deploy site --project-name ${{ vars.CF_PROJECT }} --branch production
          else
            wrangler pages deploy site --project-name ${{ vars.CF_PROJECT }} --branch pr-${{ github.event.pull_request.number }}
          fi
```

---

## 9. Interactive Embeds (Desmos & GeoGebra)

### Implementation Guidelines

- Load scripts **only** on embed pages
- Initialize on DOMContentLoaded
- Keep all computation client-side
- Lazy-load where possible

### Example Integration

```html
<!-- Only in embed templates -->
<div id="calculator" style="width:100%;height:400px"></div>
<script src="https://www.desmos.com/api/v1.8/calculator.js?apiKey=YOUR_KEY"></script>
<script>
  document.addEventListener('DOMContentLoaded', function() {
    const elt = document.getElementById('calculator');
    const calculator = Desmos.GraphingCalculator(elt);
    calculator.setExpression({ id: 'graph1', latex: 'y=x^2' });
  });
</script>
```

---

## 10. Migration Checklist

### Week 1: Foundation

- [ ] Create `content/global/` structure
- [ ] Set up `cloudflare/` directory with both header files
- [ ] Update `scripts/build.py` to generate manifest.json
- [ ] Create Cloudflare Pages project
- [ ] Wire GitHub repo to Pages

### Week 2: Content Migration

- [ ] Extract 3-5 shared policies to global
- [ ] Convert templates to use includes
- [ ] Build first embed pages
- [ ] Test CSP with local dashboard
- [ ] Deploy preview build

### Week 3: Integration

- [ ] Complete dashboard Preview Hub
- [ ] Test Blackboard iframe with one course
- [ ] Enable dedupe validation
- [ ] Set up production domain
- [ ] Full validation suite passing

### Week 4: Rollout

- [ ] Migrate remaining shared content
- [ ] Convert all courses to new structure
- [ ] Update all Blackboard embeds
- [ ] Monitor and optimize caching
- [ ] Document for next semester

---

## 11. Production Deployment Checklist

### Pre-Deploy

- [ ] All validation passing (schema, dedupe, links)
- [ ] Manifest.json generating correctly
- [ ] Both CSP profiles tested
- [ ] Dashboard Preview Hub functional
- [ ] Embed pages render without navigation

### Deploy

- [ ] Production domain configured
- [ ] SSL certificate active
- [ ] ENV=prod in build
- [ ] _headers.prod in place
- [ ] Redirects working

### Post-Deploy

- [ ] Test iframe in actual Blackboard course
- [ ] Verify CSP blocks unauthorized framing
- [ ] Check fallback links work
- [ ] Monitor error rates
- [ ] Document any issues for next iteration

---

## 12. Dependencies

```toml
[project]
requires-python = ">=3.12"
dependencies = [
  "jinja2>=3.1",
  "jsonschema>=4.21",
  "pydantic>=2.6",
  "minify-html>=0.12",
  "markdown>=3.6",
  "linkchecker>=10.4",
  "flask>=3.0",     # for dashboard only
]

[tool.uv]
dev-dependencies = [
  "pytest>=8.0",
  "black>=24.0",
  "ruff>=0.3",
]
```

---

## 13. Support & Troubleshooting

### Common Issues

**Iframe won't load in Blackboard**

- Check frame-ancestors in CSP
- Verify using /embed/ URL not full page
- Confirm HTTPS on both sides

**Preview Hub can't iframe preview builds**

- Ensure ENV=preview when building
- Check localhost:5055 in frame-ancestors
- Clear browser cache

**Desmos/GeoGebra not working**

- Verify domains in script-src and frame-src
- Check console for CSP violations
- Ensure scripts load after DOM ready

### Quick Commands

```bash
# Local development
make dashboard          # Start preview hub
make build-site ENV=preview && make preview  # Test locally

# Deployment
make deploy-preview     # Deploy PR build
make deploy-prod        # Deploy to production

# Debugging
make compare            # Compare old vs new build
make validate           # Check all schemas
make dedupe             # Find duplicate content
```

---

## Notes for Next Semester

1. Start migration 3 weeks before semester
2. Keep fall-2025 branch as reference
3. Update annual/semester variables first
4. Test with one small course completely before scaling
5. Archive previous semester to cold storage after validation
