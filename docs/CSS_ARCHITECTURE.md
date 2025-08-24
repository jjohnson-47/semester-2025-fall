# CSS Architecture Documentation

## Overview

The CSS architecture provides a layered styling system for course documents with a root stylesheet for common elements and course-specific stylesheets for unique branding and features.

## Architecture Layers

### 1. Root Stylesheet (`build/css/course.css`)

The foundation layer containing:

- **CSS Variables**: Colors, typography, spacing, layout dimensions
- **Base Styles**: Reset and default element styling
- **Typography**: Consistent heading and text styles
- **Components**: Tables, lists, info boxes, legends
- **Utilities**: Helper classes for spacing, alignment
- **Print Styles**: Optimized layout for printing
- **Responsive Design**: Mobile and tablet breakpoints

### 2. Course-Specific Stylesheets (`build/css/courses/{COURSE_CODE}.css`)

Customization layer for individual courses:

- **Color Overrides**: Course-specific color schemes
- **Thematic Elements**: Visual patterns and decorations
- **Special Components**: Course-specific content boxes
- **Assignment Badges**: Custom styling for different assignment types

### 3. Template Inline Styles

Minimal page-specific overrides in templates:

- Layout adjustments specific to syllabus vs schedule
- Container configurations
- Page-specific spacing

## CSS Variables Reference

### Global Variables (in `:root`)

```css
/* Brand Colors */
--uaa-blue: #003366;       /* University primary */
--uaa-gold: #ffc424;       /* University accent */
--kpc-green: #00695c;      /* College color */

/* Semantic Colors */
--primary-color            /* Main brand color */
--accent-color             /* Highlight color */
--success-color            /* Success states */
--warning-color            /* Warning states */
--danger-color             /* Error/danger states */

/* Typography */
--font-family-base         /* Main font stack */
--font-family-mono         /* Code font stack */
--font-size-base           /* Base font size */
--line-height-base         /* Base line height */

/* Spacing Scale */
--spacing-xs: 4px
--spacing-sm: 8px
--spacing-md: 16px
--spacing-lg: 24px
--spacing-xl: 32px
--spacing-xxl: 48px

/* Layout */
--container-max-width      /* Max container width */
--content-max-width        /* Max content width */
```

## Course Customization Guide

### Creating a New Course Style

1. Create `build/css/courses/{COURSE_CODE}.css`
2. Override CSS variables for course branding
3. Add course-specific components
4. Templates automatically load course CSS

### Example Course Stylesheet Structure

```css
/* Course identification and theme */
:root {
  --course-primary: #1a237e;
  --course-accent: #ff6f00;
  --primary-color: var(--course-primary);
  --accent-color: var(--course-accent);
}

/* Course header customization */
.course-header {
  background: linear-gradient(...);
}

/* Course-specific components */
.custom-component {
  /* Custom styles */
}

/* Assignment type styling */
.assignment-badge.custom-type {
  /* Badge styles */
}
```

## Component Library

### Info Boxes

```html
<div class="info-box">Standard info</div>
<div class="info-box important">Important notice</div>
<div class="info-box warning">Warning message</div>
<div class="info-box success">Success message</div>
<div class="info-box danger">Error/danger</div>
```

### Assignment Badges

```html
<span class="assignment-badge homework">Homework</span>
<span class="assignment-badge test">Test</span>
<span class="assignment-badge project">Project</span>
```

### Table Row States

```html
<tr class="holiday-row">Holiday week</tr>
<tr class="exam-row">Exam week</tr>
<tr class="finals-row">Finals week</tr>
```

## Course Color Schemes

### MATH221 - Calculus I

- Primary: Deep Indigo (#1a237e)
- Accent: Mathematical Orange (#ff6f00)
- Theme: Classical mathematics

### MATH251 - Calculus I (alternate section)

- Primary: Teal (#00695c)
- Accent: Deep Orange (#ff5722)
- Theme: Integration and series

### STAT253 - Applied Statistics

- Primary: Statistics Blue (#1565c0)
- Accent: Data Green (#00c853)
- Theme: Data science and analysis

## Responsive Breakpoints

### Tablet (≤768px)

- Reduced font sizes
- Simplified layout
- Condensed spacing

### Mobile (≤480px)

- Single column layout
- Minimal padding
- Stacked components

## Print Optimization

- White background
- No shadows or decorations
- Black text for readability
- Page break control
- URL display for links

## Best Practices

### Adding New Styles

1. Use CSS variables for consistency
2. Follow BEM naming for components
3. Keep specificity low
4. Test responsive behavior
5. Verify print layout

### Performance

1. Minimize inline styles
2. Use CSS variables for theming
3. Avoid deep nesting
4. Group related properties

### Maintenance

1. Document custom components
2. Use semantic class names
3. Keep course styles focused
4. Test across browsers

## File Structure

```
build/
├── css/
│   ├── course.css           # Root stylesheet
│   └── courses/
│       ├── MATH221.css      # Course-specific
│       ├── MATH251.css      # Course-specific
│       └── STAT253.css      # Course-specific
└── syllabi/
    └── *.html               # Uses both CSS files
```

## Integration with Build System

The build scripts automatically:

1. Reference the correct CSS files in generated HTML
2. Use course code to load course-specific styles
3. Maintain relative paths for portability

## Future Enhancements

- [ ] Dark mode support via CSS variables
- [ ] Animation library for transitions
- [ ] Icon font integration
- [ ] Advanced print layouts
- [ ] Accessibility improvements
