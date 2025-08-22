#!/usr/bin/env python3
"""
Dashboard Flask application factory.
Creates and configures the Flask application.
"""

from flask import Flask


def create_app(config_name=None):
    """
    Application factory pattern for Flask app creation.

    Args:
        config_name: Configuration to use (development, testing, production)

    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)

    # Load configuration
    from dashboard.config import get_config

    config = get_config(config_name)
    app.config.from_object(config)
    config.init_app(app)

    # Initialize extensions
    init_extensions(app)

    # Register blueprints
    register_blueprints(app)

    # Register error handlers
    register_error_handlers(app)

    # Register CLI commands
    register_commands(app)

    # Register template filters
    register_template_filters(app)

    return app


def init_extensions(app):
    """Initialize Flask extensions."""
    # CORS support
    from flask_cors import CORS

    CORS(app, origins=app.config.get("CORS_ORIGINS", "*"))

    # Request ID for tracking
    @app.before_request
    def before_request():
        import uuid

        from flask import g

        g.request_id = str(uuid.uuid4())

    # JSON encoder for datetime
    from flask.json.provider import DefaultJSONProvider

    class UpdatedJSONProvider(DefaultJSONProvider):
        def default(self, obj):
            from datetime import date, datetime

            if isinstance(obj, datetime | date):
                return obj.isoformat()
            return super().default(obj)

    app.json = UpdatedJSONProvider(app)


def register_blueprints(app):
    """Register application blueprints."""
    # API blueprints
    from dashboard.api import api_bp

    app.register_blueprint(api_bp, url_prefix="/api")

    # Web UI blueprints
    from dashboard.views import main_bp

    app.register_blueprint(main_bp)


def register_error_handlers(app):
    """Register error handlers."""

    @app.errorhandler(404)
    def not_found_error(_error):
        """Handle 404 errors."""
        from flask import jsonify, request

        if request.path.startswith("/api/"):
            return jsonify({"error": "Resource not found"}), 404
        from flask import render_template

        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        from flask import jsonify, request

        app.logger.error(f"Internal error: {error}")
        if request.path.startswith("/api/"):
            return jsonify({"error": "Internal server error"}), 500
        from flask import render_template

        return render_template("errors/500.html"), 500

    @app.errorhandler(400)
    def bad_request_error(_error):
        """Handle 400 errors."""
        from flask import jsonify

        return jsonify({"error": "Bad request"}), 400


def register_commands(app):
    """Register CLI commands."""

    @app.cli.command()
    def init_db():
        """Initialize the database."""
        from dashboard.services.task_service import TaskService

        TaskService.initialize_data()
        print("Database initialized.")

    @app.cli.command()
    def seed_db():
        """Seed database with sample data."""
        from dashboard.services.task_service import TaskService

        TaskService.seed_sample_data()
        print("Sample data loaded.")

    @app.cli.command()
    def reset_tasks():
        """Reset all tasks to 'todo' status."""
        from dashboard.services.task_service import TaskService

        TaskService.reset_all_tasks()
        print("All tasks reset.")


def register_template_filters(app):
    """Register custom Jinja2 template filters."""

    @app.template_filter("dateformat")
    def dateformat(value, format="%b %d, %Y"):
        """Format a date."""
        from datetime import datetime

        if isinstance(value, str):
            value = datetime.fromisoformat(value)
        return value.strftime(format) if value else ""

    @app.template_filter("status_badge")
    def status_badge(status):
        """Return CSS class for status badge."""
        badges = {
            "todo": "badge-secondary",
            "in_progress": "badge-primary",
            "completed": "badge-success",
            "blocked": "badge-danger",
            "deferred": "badge-warning",
        }
        return badges.get(status, "badge-secondary")

    @app.template_filter("priority_icon")
    def priority_icon(priority):
        """Return icon for priority level."""
        icons = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
        return icons.get(priority, "⚪")
