#!/usr/bin/env python3
"""
Web views blueprint initialization.
"""

from flask import Blueprint

# Create main blueprint for web views
main_bp = Blueprint("main", __name__)

# Import routes after blueprint creation
from dashboard.views import main
