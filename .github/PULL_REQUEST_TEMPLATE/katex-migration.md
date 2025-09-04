## KaTeX Migration: A δ for your ε

### Summary
- Replace MathJax with local KaTeX for robust, synchronous math rendering
- Vendor KaTeX assets under `site/interactive/_vendor/katex/`
- Add `js/math-render.js` helper (auto-render wrapper)
- Update `epsilon-delta.html` to load KaTeX locally
- Update `epsilon-delta.js` to use KaTeX render calls for dynamic content

### Changes
- Added: `site/interactive/math251/js/math-render.js`
- Updated: `site/interactive/math251/epsilon-delta.html` (head includes)
- Updated: `site/interactive/math251/js/epsilon-delta.js` (renderMathTargets)
- Added: `Makefile` targets `vendor-katex`, `sprint-katex`, `dev-serve`, `test-e2e`
- Added: `cypress/e2e/epsilon-delta.cy.js` (seed test)

### How to Test
1. `npm install katex@^0.16.10` (and `npm install cypress --save-dev` for e2e)
2. `make vendor-katex`
3. `make dev-serve` then open `http://localhost:8002/epsilon-delta.html`
4. Verify math renders without network
5. Run `make test-e2e` to execute Cypress seed test

### Acceptance Criteria
- [ ] Tool renders math offline (KaTeX from `_vendor/`)
- [ ] Dynamic updates (guidance, notifications) render math correctly
- [ ] Canvas renders on first paint and on resize
- [ ] Seed Cypress test passes

### Notes
- This migration removes runtime dependency on MathJax/CDNs and simplifies startup
- If advanced MathJax features are required later, we can vendor MathJax locally instead

