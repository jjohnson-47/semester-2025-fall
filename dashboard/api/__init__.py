#!/usr/bin/env python3
"""
API Blueprint initialization.
Provides RESTful API endpoints for the dashboard.
"""

from flask import Blueprint

# Create API blueprint
api_bp = Blueprint("api", __name__)

# Import routes after blueprint creation to avoid circular imports
# These imports register routes with the blueprint
from dashboard.api import courses as courses  # noqa: E402
from dashboard.api import export as export  # noqa: E402
from dashboard.api import stats as stats  # noqa: E402
from dashboard.api import tasks as tasks  # noqa: E402
from dashboard.api import tasks_htmx as tasks_htmx  # noqa: E402

# The imports above are intentionally kept to register their routes
# with the api_bp blueprint through side effects
