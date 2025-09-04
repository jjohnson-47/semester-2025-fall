#!/usr/bin/env python3
"""Style system integration for v2 architecture.

Provides a proper architectural approach to CSS management that:
- Integrates with the template rendering system
- Supports both local and production deployment contexts  
- Maintains course-specific styling paradigm
- Embeds styles inline for standalone HTML files
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any


class DeploymentContext(Enum):
    """Deployment context for style rendering."""
    LOCAL = "local"        # Standalone HTML files with embedded CSS
    PRODUCTION = "production"  # Site deployment with external CSS files
    IFRAME = "iframe"      # Blackboard iframe embedding


@dataclass
class StyleConfiguration:
    """Style system configuration."""
    deployment_context: DeploymentContext = DeploymentContext.LOCAL
    base_css_path: Path = Path("assets/css/course.css")
    courses_css_dir: Path = Path("assets/css/courses")
    embed_styles: bool = True  # For LOCAL context
    use_cdn_fonts: bool = True

    def should_embed(self) -> bool:
        """Determine if styles should be embedded inline."""
        return self.deployment_context == DeploymentContext.LOCAL and self.embed_styles


class StyleSystem:
    """Manages styles for course material generation.
    
    This is the proper architectural component for CSS management in v2.
    It integrates with the template system to provide context-aware styling.
    """

    # Course-specific color themes (Blackboard-compatible)
    COURSE_COLORS = {
        "MATH221": {
            "primary": "#0066cc",      # Blue
            "primary_light": "#3399ff",
            "primary_dark": "#004499",
            "accent": "#009900",        # Green
        },
        "MATH251": {
            "primary": "#006600",      # Green
            "primary_light": "#339933",
            "primary_dark": "#004400",
            "accent": "#0066cc",        # Blue
        },
        "STAT253": {
            "primary": "#cc6600",      # Orange
            "primary_light": "#ff9933",
            "primary_dark": "#994400",
            "accent": "#006666",        # Teal
        }
    }

    def __init__(self, config: StyleConfiguration | None = None):
        """Initialize style system.
        
        Args:
            config: Style configuration, defaults to LOCAL deployment
        """
        self.config = config or StyleConfiguration()

    def get_template_style_context(self, course_code: str) -> dict[str, Any]:
        """Get style context for template rendering.
        
        This is the main integration point with the template system.
        It provides all necessary style information based on deployment context.
        
        Args:
            course_code: Course identifier (e.g., MATH221)
            
        Returns:
            Dictionary with style-related template variables:
            - style_mode: 'embedded' or 'linked'
            - base_css_content: Embedded CSS content (if embedding)
            - course_css_content: Course-specific CSS (if embedding)
            - base_css_path: Path to base CSS (if linking)
            - course_css_path: Path to course CSS (if linking)
            - font_imports: Font import HTML
        """
        context = {
            'style_mode': 'embedded' if self.config.should_embed() else 'linked',
            'font_imports': self._get_font_imports(),
        }

        if self.config.should_embed():
            # For local deployment, embed CSS inline for standalone HTML
            context.update({
                'base_css_content': self._load_base_css(),
                'course_css_content': self._load_course_css(course_code),
                'has_embedded_styles': True,
            })
        else:
            # For production deployment, use external CSS files
            context.update({
                'base_css_path': self._get_css_path('course.css'),
                'course_css_path': self._get_css_path(f'courses/{course_code}.css'),
                'has_embedded_styles': False,
            })

        return context

    def _load_base_css(self) -> str:
        """Load base CSS content for embedding."""
        if self.config.base_css_path.exists():
            return self.config.base_css_path.read_text(encoding='utf-8')
        return self._get_fallback_css()

    def _load_course_css(self, course_code: str) -> str:
        """Load course-specific CSS content for embedding."""
        # First check for an existing course CSS file
        course_css = self.config.courses_css_dir / f"{course_code}.css"
        if course_css.exists():
            return course_css.read_text(encoding='utf-8')

        # Generate course-specific CSS from color themes
        if course_code in self.COURSE_COLORS:
            colors = self.COURSE_COLORS[course_code]
            return f"""
/* Course-specific styles for {course_code} */
:root {{
    --color-primary: {colors['primary']};
    --color-primary-light: {colors['primary_light']};
    --color-primary-dark: {colors['primary_dark']};
    --accent-color: {colors['accent']};
    --course-theme-primary: {colors['primary']};
    --course-theme-accent: {colors['accent']};
}}

/* Course-specific header styling */
h1, h2 {{
    color: var(--course-theme-primary);
}}

.syllabus-container h1 {{
    border-bottom: 3px solid var(--course-theme-primary);
}}

.important-dates {{
    border-left-color: var(--course-theme-accent);
}}

/* Links in course colors */
a {{
    color: var(--course-theme-primary);
}}

a:hover {{
    color: var(--color-primary-dark);
}}

/* Table headers */
th {{
    background-color: var(--bg-secondary);
    color: var(--course-theme-primary);
}}

/* Evaluation table styling */
.evaluation-table th {{
    background-color: var(--course-theme-primary);
    color: white;
}}
"""
        return ""  # Course-specific CSS is optional

    def _get_css_path(self, relative_path: str) -> str:
        """Get CSS path based on deployment context."""
        if self.config.deployment_context == DeploymentContext.PRODUCTION:
            return f"/assets/css/{relative_path}"
        elif self.config.deployment_context == DeploymentContext.IFRAME:
            # For iframe, use absolute URLs to production site
            return f"https://courses.jeffsthings.com/assets/css/{relative_path}"
        else:
            # Local context - relative paths
            return f"assets/css/{relative_path}"

    def _get_font_imports(self) -> str:
        """Get font import HTML based on configuration."""
        if not self.config.use_cdn_fonts:
            return ""

        return """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Open+Sans:ital,wght@0,300;0,400;0,600;0,700;1,400&display=swap" rel="stylesheet">"""

    def _get_fallback_css(self) -> str:
        """Provide minimal fallback CSS if files are missing."""
        return """
/* Fallback styles for v2 architecture */
:root {
    --font-family-primary: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    --font-size-base: 1rem;
    --color-primary: #0066cc;
    --color-text: #333;
    --bg-primary: #ffffff;
    --spacing-xs: 0.5rem;
    --spacing-sm: 0.75rem;
    --spacing-md: 1rem;
    --spacing-lg: 1.5rem;
    --spacing-xl: 2rem;
    --content-max-width: 65ch;
    --border-radius: 0.375rem;
}

body {
    font-family: var(--font-family-primary);
    font-size: var(--font-size-base);
    color: var(--color-text);
    line-height: 1.6;
    max-width: var(--content-max-width);
    margin: 0 auto;
    padding: var(--spacing-lg);
}

h1, h2, h3, h4, h5, h6 {
    margin-top: var(--spacing-lg);
    margin-bottom: var(--spacing-md);
    font-weight: 600;
}

h1 { 
    color: var(--color-primary);
    border-bottom: 2px solid var(--color-primary);
    padding-bottom: 0.5rem;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: var(--spacing-md) 0;
}

th, td {
    padding: 0.5rem;
    text-align: left;
    border-bottom: 1px solid #ddd;
}

th {
    background: #f5f5f5;
    font-weight: 600;
}

.info-box, .important-dates {
    background: #f8f9fa;
    border-left: 4px solid var(--color-primary);
    padding: var(--spacing-md);
    padding-left: var(--spacing-lg);  /* Extra space after border for better visual separation */
    margin: var(--spacing-md) 0;
    border-radius: var(--border-radius);
}
"""
