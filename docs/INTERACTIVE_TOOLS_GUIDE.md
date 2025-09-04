# Interactive Tools Development Guide
## Fall 2025 Semester Management System

**Last Updated:** January 2025  
**Version:** 1.0  
**Status:** Production Ready

## Overview

This document captures lessons learned and best practices from developing interactive HTML tools for mathematics education, specifically the “A δ for your ε” tool for MATH 251 Calculus I.

## Project Structure

```
semester-2025-fall/
├── site/
│   └── interactive/
│       └── math251/
│           ├── index.html              # Tool hub page
│           ├── epsilon-delta.html      # Main interactive tool (STABLE)
│           ├── epsilon-delta-stable.html  # Development backup
│           ├── epsilon-delta-backup.html  # Original backup
│           ├── iframe-test.html        # Iframe testing page
│           └── css/
│               └── main.css           # Shared styles
```

## Tool Details: A δ for your ε

### Location and Purpose
- **Path:** `/site/interactive/math251/epsilon-delta.html`
- **Purpose:** Interactive visualization tool for teaching the epsilon-delta definition of limits
- **Target Course:** MATH 251 - Calculus I
- **Deployment:** Blackboard Ultra iframe embedding
- **Production URL:** `https://courses.jeffsthings.com/interactive/math251/epsilon-delta.html`

### Technical Specifications
- **Technology Stack:** HTML5 Canvas, Vanilla JavaScript, KaTeX (vendored), CSS3
- **Canvas Dimensions:** 600×400 pixels (fixed for stability)
- **Font System:** Inter (UI) + JetBrains Mono (code/math)
- **Color Scheme:** MATH251 Green (#006600) with variants
- **Responsive:** Yes, with mobile breakpoints

### Educational Features
1. **Three Learning Modes:**
   - **Learn Mode:** Step-by-step guided instruction
   - **Practice Mode:** Self-directed problem solving
   - **Challenge Mode:** Timed progression through all levels

2. **Five Function Levels:**
   - Linear: f(x) = 2x + 1
   - Quadratic: f(x) = x²
   - Sine: f(x) = sin(x)
   - Cubic: f(x) = x³
   - Reciprocal: f(x) = 1/x

3. **Interactive Elements:**
   - Epsilon (ε) slider for error tolerance
   - Delta (δ) slider for input range
   - Real-time graph visualization
   - Visual feedback indicators
   - Progress tracking and scoring

## Critical Lessons Learned

### 1. Canvas Rendering Stability

**Problem:** Canvas would frequently fail to render, showing blank graphs or dimensional errors.

**Root Cause:** Inconsistent canvas sizing and initialization timing.

**Solution:**
```javascript
// ✅ CORRECT: Fixed dimensions with proper initialization
function initCanvas() {
    const canvas = document.getElementById('graphCanvas');
    
    // Set actual canvas size (NOT CSS size)
    canvas.width = 600;
    canvas.height = 400;
    
    // Set display size via CSS
    canvas.style.width = '100%';
    canvas.style.maxWidth = '600px';
    canvas.style.height = '400px';
    
    console.log(`Canvas initialized: ${canvas.width}x${canvas.height}`);
}

// Use requestAnimationFrame for smooth updates
function updateGraph() {
    requestAnimationFrame(drawGraph);
}
```

**❌ What NOT to do:**
- Rely on CSS-only sizing
- Use dynamic canvas dimensions
- Skip canvas context validation
- Call draw functions before DOM ready

### 2. Math Rendering

Note: KaTeX (vendored locally) is the default math renderer for the epsilon–delta tool. The following MathJax notes are retained for legacy reference only.

**Problem:** Mathematical notation would render inconsistently or disappear entirely.

**Root Cause:** Improper MathJax configuration and re-rendering issues.

**Solution:**
```javascript
// ✅ CORRECT: Stable MathJax configuration
window.MathJax = {
    tex: {
        inlineMath: [['$', '$'], ['\\(', '\\)']],
        displayMath: [['$$', '$$'], ['\\[', '\\]']]
    },
    startup: {
        ready: () => {
            MathJax.startup.defaultReady();
            MathJax.startup.promise.then(() => {
                console.log('MathJax ready');
            });
        }
    }
};

// Re-render after dynamic content changes
if (window.MathJax && MathJax.typesetPromise) {
    MathJax.typesetPromise().catch(e => console.log('MathJax error:', e));
}
```

**❌ What NOT to do:**
- Use deprecated polyfill.io
- Call MathJax before it's loaded
- Skip error handling in typesetPromise

### 3. Mode Functionality Implementation

**Problem:** Mode buttons existed but didn't actually change application behavior.

**Root Cause:** Missing mode-specific logic and content switching.

**Solution:**
```javascript
// ✅ CORRECT: Functional mode switching
function setMode(mode) {
    gameState.mode = mode;
    
    // Update button states
    document.querySelectorAll('.mode-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.mode === mode);
    });
    
    // Show/hide mode-specific content
    document.getElementById('learnContent').classList.toggle('active', mode === 'learn');
    document.getElementById('practiceContent').classList.toggle('active', mode === 'practice');
    document.getElementById('challengeContent').classList.toggle('active', mode === 'challenge');
    
    // Mode-specific behavior
    if (mode === 'learn') {
        updateGuidance();
    }
}
```

**Key Principle:** Every UI element must have corresponding functional behavior.

### 4. Interactive Learning Design

**Problem:** "Learn Mode" wasn't actually teaching - just displaying the same interface.

**Solution:** Progressive, context-aware guidance:
```javascript
function updateGuidance() {
    if (gameState.mode !== 'learn') return;
    
    const level = gameState.levels[gameState.currentLevel];
    const guidanceText = document.querySelector('#learnContent .guidance-text');
    
    if (gameState.guidanceStep === 0) {
        guidanceText.innerHTML = `
            <strong>Step 1:</strong> We have the function ${level.funcStr}...
            First, adjust the <strong>epsilon (ε)</strong> slider...
        `;
        gameState.guidanceStep = 1;
    } else if (gameState.guidanceStep === 1 && delta > 0.05) {
        guidanceText.innerHTML = `
            <strong>Step 2:</strong> Good! Now adjust the <strong>delta (δ)</strong> slider...
            <em>Hint: ${level.hint}</em>
        `;
        gameState.guidanceStep = 2;
    }
}
```

### 5. Error Handling and Robustness

**Problem:** Tool would break with division by zero, invalid function values, or missing elements.

**Solution:** Comprehensive error handling:
```javascript
// ✅ CORRECT: Robust function evaluation
for (let i = 0; i <= 200; i++) {
    const x = xMin + (i / 200) * (xMax - xMin);
    
    // Skip problematic points
    if (Math.abs(x - level.xStar) < 0.001) continue;
    
    try {
        const y = level.func(x);
        
        // Validate result
        if (!isNaN(y) && isFinite(y)) {
            // Safe to use y
        }
    } catch (e) {
        // Handle errors gracefully
        firstPoint = true;
    }
}
```

## Development Workflow Best Practices

### 1. Incremental Development
- Start with basic canvas rendering
- Add one feature at a time
- Test thoroughly before adding complexity
- Maintain working backups at each stage

### 2. Testing Strategy
- Test in different browsers (Chrome, Firefox, Safari)
- Test iframe embedding specifically
- Test on mobile devices
- Test with slow network connections

### 3. Version Control
- Keep working versions as backups
- Use descriptive commit messages
- Tag stable releases
- Document breaking changes

## Deployment Considerations

### 1. Iframe Compatibility
```html
<!-- ✅ CORRECT: Production iframe code -->
<iframe 
    src="https://courses.jeffsthings.com/interactive/math251/epsilon-delta.html" 
    width="100%" 
    height="800" 
    frameborder="0" 
    allowfullscreen>
</iframe>
```

### 2. Security Headers
- Ensure CSP allows iframe embedding
- Test from Blackboard Ultra environment
- Verify HTTPS deployment

### 3. Performance
- Minimize external dependencies
- Prefer vendored KaTeX locally for offline reliability; use Google Fonts via CDN
- Optimize canvas drawing operations
- Cache static assets

## Educational Tool Design Principles

### 1. Progressive Disclosure
- Start simple, add complexity gradually
- Provide multiple learning paths
- Allow self-paced exploration

### 2. Immediate Feedback
- Visual indicators for correct/incorrect
- Real-time graph updates
- Clear success/failure states

### 3. Scaffolded Learning
- Learn Mode: Guided instruction
- Practice Mode: Independent work
- Challenge Mode: Assessment

## Maintenance Guidelines

### 1. Regular Updates
- If using MathJax elsewhere, review CDN links periodically (legacy guidance)
- Test with new browser versions
- Review accessibility compliance

### 2. Content Updates
- Add new function examples
- Refine hint text based on usage
- Improve error messages

### 3. Analytics Integration
- Track completion rates
- Monitor error occurrences
- Gather user feedback

## Future Enhancements

### Planned Features
1. **Save Progress:** LocalStorage persistence
2. **Export Results:** PDF generation of work
3. **Adaptive Difficulty:** AI-based level adjustment
4. **Collaboration:** Multi-user problem solving

### Technical Improvements
1. **WebGL Canvas:** Better performance for complex functions
2. **PWA Features:** Offline functionality
3. **WebAssembly:** High-performance calculations
4. **Accessibility:** Screen reader support

## Common Pitfalls to Avoid

### ❌ Don't Do This
1. **Canvas Sizing:** Using only CSS dimensions
2. **Event Handlers:** Adding multiple listeners to same element
3. **MathJax:** Calling render before initialization
4. **Debugging:** Leaving console.log statements in production
5. **Mode Switching:** UI changes without functional changes
6. **Error Handling:** Assuming functions always work
7. **Performance:** Drawing entire canvas on every update

### ✅ Do This Instead
1. **Canvas Sizing:** Set both canvas.width/height AND CSS
2. **Event Handlers:** Remove old listeners before adding new ones
3. **MathJax:** Wait for startup.promise
4. **Debugging:** Use proper debugging tools, remove console output
5. **Mode Switching:** Change both UI and application behavior
6. **Error Handling:** Wrap all calculations in try/catch
7. **Performance:** Use requestAnimationFrame and optimize drawing

## Reference Implementation

The epsilon-delta tool serves as the reference implementation for future interactive tools. Key files:

- **Production:** `site/interactive/math251/epsilon-delta.html`
- **Backup:** `site/interactive/math251/epsilon-delta-stable.html`
- **Testing:** `site/interactive/math251/iframe-test.html`

## Contact and Support

For questions about this implementation or guidance on new interactive tools:

- **Repository:** `/home/verlyn13/Projects/jjohnson-47/semester-2025-fall`
- **Documentation:** `docs/INTERACTIVE_TOOLS_GUIDE.md`
- **Test URL:** http://localhost:8002/math251/epsilon-delta.html

---

*This document should be updated with each major tool development to capture new lessons learned and best practices.*
