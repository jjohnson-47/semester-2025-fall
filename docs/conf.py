#!/usr/bin/env python3
"""
Sphinx documentation configuration for Fall 2025 Dashboard.

This configuration enables automatic API documentation generation from
docstrings using autodoc and Napoleon extensions.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Project information
project = "Fall 2025 Dashboard"
copyright = "2025, Course Management Team"
author = "Course Management Team"
release = "2.0.0"

# Extensions
extensions = [
    "sphinx.ext.autodoc",  # Auto-generate from docstrings
    "sphinx.ext.napoleon",  # Support Google/NumPy style docstrings
    "sphinx.ext.viewcode",  # Add source code links
    "sphinx.ext.intersphinx",  # Link to other projects' docs
    "sphinx.ext.coverage",  # Check documentation coverage
    "sphinx.ext.todo",  # Support TODO directives
    "sphinx.ext.githubpages",  # GitHub Pages support
    "myst_parser",  # Markdown support
]

# Napoleon settings for docstring parsing
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_type_aliases = None

# Autodoc settings
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": True,
    "exclude-members": "__weakref__",
    "show-inheritance": True,
}
autodoc_typehints = "description"
autodoc_typehints_format = "short"

# Intersphinx - link to other documentation
intersphinx_mapping = {
    "python": ("https://docs.python.org/3.13", None),
    "flask": ("https://flask.palletsprojects.com/en/stable/", None),
    "pytest": ("https://docs.pytest.org/en/stable/", None),
}

# Add support for Markdown files
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

# Master document
master_doc = "index"

# Language
language = "en"

# Exclude patterns
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "reference"]

# HTML output options
html_theme = "sphinx_rtd_theme"  # Read the Docs theme
html_static_path = ["_static"]
html_css_files = ["custom.css"]

# HTML theme options
html_theme_options = {
    "navigation_depth": 4,
    "collapse_navigation": False,
    "sticky_navigation": True,
    "includehidden": True,
    "titles_only": False,
    "display_version": True,
    "prev_next_buttons_location": "bottom",
}

# Output formats
htmlhelp_basename = "Fall2025Dashboarddoc"

# LaTeX output
latex_elements = {
    "papersize": "letterpaper",
    "pointsize": "10pt",
    "preamble": "",
    "figure_align": "htbp",
}

latex_documents = [
    (
        master_doc,
        "Fall2025Dashboard.tex",
        "Fall 2025 Dashboard Documentation",
        "Course Management Team",
        "manual",
    ),
]

# Man page output
man_pages = [(master_doc, "fall2025dashboard", "Fall 2025 Dashboard Documentation", [author], 1)]

# Texinfo output
texinfo_documents = [
    (
        master_doc,
        "Fall2025Dashboard",
        "Fall 2025 Dashboard Documentation",
        author,
        "Fall2025Dashboard",
        "Task management system for course preparation.",
        "Miscellaneous",
    ),
]

# EPUB output
epub_title = project
epub_exclude_files = ["search.html"]

# TODO extension
todo_include_todos = True

# Coverage extension
coverage_show_missing_items = True

# Suppress specific warnings
suppress_warnings = ["autodoc.import_error"]
