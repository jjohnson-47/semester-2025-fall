#!/usr/bin/env python3
"""
Dashboard Flask application factory.
Creates and configures the Flask application.
"""

from datetime import UTC
from typing import Any, cast

from flask import Flask


def create_app(config_name: str | None = None) -> Flask:
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


def init_extensions(app: Flask) -> None:
    """Initialize Flask extensions."""
    # CORS support
    from flask_cors import CORS

    CORS(app)


def register_blueprints(app: Flask) -> None:
    """Register all blueprints."""
    # Main views
    from dashboard.views import main_bp

    app.register_blueprint(main_bp)

    # API blueprints
    from dashboard.api import api_bp

    app.register_blueprint(api_bp, url_prefix="/api")


def register_error_handlers(app: Flask) -> None:
    """Register error handlers."""

    @app.errorhandler(404)
    def not_found_error(error: Any) -> tuple[dict[str, str], int]:  # noqa: ARG001
        """Handle 404 errors."""
        from flask import jsonify, request

        if request.path.startswith("/api/"):
            return jsonify({"error": "Not found"}), 404
        from flask import render_template

        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(error: Any) -> tuple[dict[str, str], int]:
        """Handle 500 errors."""
        from flask import jsonify, request

        app.logger.error(f"Internal error: {error}")
        if request.path.startswith("/api/"):
            return jsonify({"error": "Internal server error"}), 500
        from flask import render_template

        return render_template("errors/500.html"), 500


def register_commands(app: Flask) -> None:
    """Register CLI commands."""
    import click

    @app.cli.command()
    @click.option("--course", help="Course code to generate tasks for")
    def generate_tasks(course: str | None) -> None:
        """Generate tasks from templates."""
        # TODO: Add proper paths for courses and templates
        # For now, just show a placeholder message
        if course:
            click.echo(f"Generating tasks for {course}...")
            click.echo("Task generation not yet implemented in this context")
        else:
            click.echo("Generating tasks for all courses...")
            click.echo("Task generation not yet implemented in this context")

    @app.cli.command()
    def init_db() -> None:
        """Initialize the database."""
        click.echo("Initializing database...")
        # Implementation here

    @app.cli.command()
    def seed_data() -> None:
        """Seed sample data (DB-backed)."""
        from dashboard.db import Database, DatabaseConfig
        from pathlib import Path as _P
        db = Database(DatabaseConfig(_P("dashboard/state/tasks.db")))
        db.initialize()
        db.create_task({"course":"MATH221","title":"Prepare syllabus","status":"todo","category":"setup"})
        click.echo("Sample data seeded (DB)")


def register_template_filters(app: Flask) -> None:
    """Register custom Jinja2 filters."""

    @app.template_filter("dateformat")
    def dateformat(value: Any, format: str = "%B %d, %Y") -> str:
        """Format a date for display."""
        from datetime import datetime

        if isinstance(value, str):
            value = datetime.fromisoformat(value)
        return value.strftime(format) if value else ""

    @app.template_filter("statusicon")
    def statusicon(status: str) -> str:
        """Get icon for task status."""
        icons = {
            "todo": "○",
            "in_progress": "◐",
            "done": "●",
            "blocked": "⊘",
        }
        return icons.get(status, "?")

    @app.template_filter("prioritycolor")
    def prioritycolor(priority: str) -> str:
        """Get color class for priority."""
        colors = {
            "critical": "danger",
            "high": "warning",
            "medium": "info",
            "low": "secondary",
        }
        return colors.get(priority, "secondary")

    @app.template_filter("markdown")
    def markdown_filter(text: str) -> str:
        """Render markdown to HTML."""
        import markdown as md  # type: ignore[import-untyped]

        return md.markdown(text) if text else ""

    @app.template_filter("timeago")
    def timeago(dt: Any) -> str:
        """Format datetime as time ago."""
        from datetime import datetime

        if isinstance(dt, str):
            dt = datetime.fromisoformat(dt)

        if not dt:
            return ""


        now = datetime.now(UTC)
        if dt.tzinfo is None:
            from pytz import UTC as pytz_UTC  # type: ignore[import-untyped]

            dt = pytz_UTC.localize(dt)

        diff = now - dt
        if diff.days > 7:
            return cast(str, dt.strftime("%B %d, %Y"))
        elif diff.days > 0:
            return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "just now"
