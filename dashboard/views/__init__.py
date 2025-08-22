#!/usr/bin/env python3
"""
Web views blueprint initialization.
"""

from flask import Blueprint

# Create main blueprint for web views
main_bp = Blueprint("main", __name__)

# Import routes after blueprint creation to register them
from dashboard.views import main as main  # noqa: E402, F401

# The import above is required to register routes with the blueprint
