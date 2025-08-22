#!/usr/bin/env python3
"""
API Blueprint initialization.
Provides RESTful API endpoints for the dashboard.
"""

from flask import Blueprint

# Create API blueprint
api_bp = Blueprint("api", __name__)

# Import routes after blueprint creation to avoid circular imports
from dashboard.api import courses, export, stats, tasks

# Register sub-blueprints if needed
# api_bp.register_blueprint(tasks.tasks_bp, url_prefix='/tasks')
