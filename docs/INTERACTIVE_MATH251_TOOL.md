# A δ for your ε — MATH 251 Interactive Tool

Comprehensive documentation for the MATH 251 interactive limits tool. Covers project structure, build/tooling, runtime architecture, UX/UI details, performance, accessibility, embedding, and operations.

## Overview

- **Purpose:** Teach the epsilon–delta definition of limits with an interactive, proof‑minded experience that works in Blackboard Ultra iframes and as a standalone web tool.
- **Name:** “A δ for your ε” (formerly “Epsilon‑Delta Master”).
- **Host strategy:** Fully static; no secrets. Optimized for Cloudflare Pages and Blackboard embedding. Supports local/offline vendor assets for deterministic rendering.

## Project Structure

Root location of the tool within the repo:

```
site/interactive/math251/
├── index.html                    # Hub page (cards, badges, help)
├── epsilon-delta.html            # Main tool page (A δ for your ε)
├── iframe-test.html              # Embedding instructions + live iframe
├── assets/
│   └── favicon.svg               # Tool favicon
├── css/
│   ├── main.css                  # Shared theme, shell, components
│   ├── epsilon-delta.css         # Extracted page styles (baseline)
│   └── epsilon-delta-improved.css# Improved contrast/iteration stylesheet
└── js/
    ├── core.js                   # MATH251Core: storage, events, focus ring, toasts
    ├── progress.js               # Progress helpers (namespaced localStorage)
    ├── epsilon-delta.js          # Main tool logic (now using KaTeX via renderMathTargets)
    └── math-render.js            # KaTeX wrapper for math rendering (vendored locally)
```

Optionally vendor local render engines (recommended for reliability):

```
site/interactive/_vendor/
└── katex/                        # Now using KaTeX (vendored locally, was MathJax)
    ├── katex.min.css
    ├── katex.min.js
    ├── contrib/auto-render.min.js
    └── fonts/*
```

## Build, Run, and Tooling

- **Local preview:** `cd site/interactive/math251 && python -m http.server 8002`
- **Visit:** `http://localhost:8002/math251/epsilon-delta.html` (tool) or `/math251/index.html` (hub)
- **Make targets (repo‑wide):** see `make help` for lint/format/test; prefer `make validate` for JSON, `make test` for Python libs.
- **Vendor assets:**
  - KaTeX files are now vendored locally under `site/interactive/_vendor/` (no CDN dependencies).
  - Consider a small Make target (e.g., `make vendor-katex`) to fetch or update assets once per semester.

## Runtime Architecture

- **Shell:** All pages share a consistent shell via `css/main.css`
  - `#app-container` → `.tool-header` → `.tool-content` → `.tool-footer`
  - Keyboard skip link and focus ring (only for keyboard users)

- **Core utilities (`js/core.js`):**
  - **Storage:** Namespaced `localStorage` (`math251.interactive:*`)
  - **Event bus:** Simple pub/sub
  - **Focus ring:** Adds `focus-ring` class on Tab key
  - **Toasts:** Lightweight notifications (non-blocking)

- **Progress (`js/progress.js`):**
  - Stores `currentLevel`, `score`, `completedLevels`, `totalLevels` under `math251.interactive:progress.{tool}`
  - Hub card shows a progress badge `Level X/N` when present
  - Reset available from tool and hub

- **Math rendering:** Now using KaTeX (vendored locally)
  - Fast, synchronous rendering with no network dependencies
  - `math-render.js` helper renders dynamic fragments instantly
  - MathJax can be used locally if needed, but KaTeX is now the default

- **Graphing and state (`js/epsilon-delta.js`):**
  - **Game state:** `mode`, `currentLevel`, `score`, `completedLevels`, `levels[]`
  - **Levels:** Each has `func`, `funcLatex`, `xStar`, `limit`, `epsilonRange`, and a **validator** function that encodes the ε→δ proof strategy
  - **Canvas rendering:**
    - Scales by `devicePixelRatio` for crisp lines
    - Uses `requestAnimationFrame(drawGraph)` for smooth updates
    - Reinitializes on resize
  - **Math updates:** Calls the math engine’s typeset/render for dynamic fragments (hints, guidance, headers)

## UX & UI Design

- **Learning Modes:**
  - **Learn:** Guided steps; progressive hints; context‑aware guidance text
  - **Practice:** Independent play with instant visual feedback
  - **Challenge:** Progression through 5 function levels with scoring

- **Controls:**
  - Sliders for ε (vertical band) and δ (horizontal band)
  - “Check Answer”, “Get Hint”, “Next Level” CTA group
  - Visual status indicator with success/error animations

- **Mode selector:**
  - ARIA tabs: role=tablist; buttons role=tab; aria-selected; keyboard Left/Right to switch
  - Panels use role=tabpanel with `hidden` toggling

- **Guidance system:**
  - Updates explanatory text based on epsilon/ delta and validator results
  - Renders math inside guidance via the chosen math engine

- **Notifications:**
  - Toasts appear on correct/incorrect actions and mode switches; math enabled inside toasts

- **Hub UX:**
  - Cards for each tool; “Last visited” badge; per‑tool progress badge
  - Help modal with embedding instructions and copy‑to‑clipboard iframe code
  - Compact “Reset progress” action

## Accessibility

- **Keyboard navigation:**
  - Skip to content link
  - Focus ring only for keyboard users
  - Tab/Shift+Tab into mode tabs and content; Arrow keys switch tabs

- **ARIA:**
  - Mode buttons: role=tab, aria-selected, aria-controls
  - Panels: role=tabpanel, `hidden` attribute for non‑active

- **Status regions:**
  - Notifications and dynamic values use polite updates

## Performance

- **Canvas sizing:**
  - Fixed logical CSS size (~600×400) with DPR‑scaled backing store for crispness
  - Draw only within the graph viewport; use affordable sampling resolution

- **Render scheduling:**
  - `requestAnimationFrame` for redraws on slider change and level transitions
  - Redraw on ResizeObserver (planned) or window resize

- **Math engine:**
  - Using KaTeX for instant, synchronous rendering and low overhead
  - Vendored locally with no runtime CDN loads

## Embedding & Headers

- **Iframe embed (production):**
  - `https://courses.jeffsthings.com/interactive/math251/epsilon-delta.html`
  - Blackboard Ultra: add via HTML block (provided in hub modal and iframe-test page)

- **Security headers (edge/server):**
  - Set `X-Frame-Options` or better CSP `frame-ancestors` at the server/edge (Cloudflare Pages/Worker)
  - Example CSP: `frame-ancestors https://*.blackboard.com https://*.alaska.edu https://courses.jeffsthings.com;`

- **Caching:**
  - Long‑cache vendor assets (KaTeX), fonts, and CSS

## Operations & Reliability

- **Avoid CDNs (recommended):** Vendor math engine locally to remove third‑party dependency and race conditions
- **Diagnostics:** Consider adding a `?debug=1` overlay showing engine load status and source (local/CDN)
- **Fallbacks:**
  - KaTeX loads synchronously from local vendor path (no fallback needed)
  - Math renders instantly with no loading delay

## Roadmap

- **✅ KaTeX Migration Complete:**
  - Added `_vendor/katex/` with vendored assets
  - Created `js/math-render.js` helper
  - Replaced MathJax calls with synchronous `renderMathTargets`
  - Math renders instantly with no network dependencies

- **ResizeObserver:**
  - Replace window resize with container‑aware observer to reinit canvas

- **More Tools:**
  - Derivative visualizer, integration explorer, function grapher using same shell

## Developer Notes

- **Style:** See `css/main.css` for theme variables, cards, buttons, modals, notifications, focus styles
- **Naming:** Use descriptive function names; 4‑space indentation (Python), 2‑space (web)
- **Testing:** Manual check in a local server; verify math renders with no network if vendor assets exist
- **Docs:** Keep README and this doc updated when structure or behavior changes

## Quick Verification Checklist

- Hub shows “Last visited” and progress badge
- ε–δ renders math in headers, guidance, and toasts
- Sliders update graph and guidance in real‑time
- Keyboard users can switch modes via arrow keys
- Iframe embed works in Blackboard; no console security errors
