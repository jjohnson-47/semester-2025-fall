#!/usr/bin/env python3
"""
WSGI entry point for production deployment.
Flask 3.x compliant.
"""

import os

from dashboard import create_app

# Get configuration from environment
config_name = os.environ.get("FLASK_ENV", "production")

# Create application instance
app = create_app(config_name)

if __name__ == "__main__":
    # Only for development - use proper WSGI server in production
    app.run(
        host=app.config.get("HOST", "0.0.0.0"),
        port=app.config.get("PORT", 5000),
        debug=app.config.get("DEBUG", False),
    )
