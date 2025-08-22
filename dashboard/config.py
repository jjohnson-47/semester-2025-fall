#!/usr/bin/env python3
"""
Flask application configuration.
Provides different configuration classes for development, testing, and production.
"""

import os
from datetime import timedelta
from pathlib import Path
from typing import Any

# Load .env file if available
try:
    from dotenv import load_dotenv

    # Load base config
    load_dotenv()

    # Load secrets if available
    secrets_file = Path(".env.secrets")
    if secrets_file.exists():
        load_dotenv(secrets_file)
except ImportError:
    pass  # dotenv not available, use system env vars


class Config:
    """Base configuration with common settings."""

    # Basic Flask config
    # Support both SECRET_KEY and FLASK_SECRET_KEY for flexibility
    SECRET_KEY = (
        os.environ.get("FLASK_SECRET_KEY")
        or os.environ.get("SECRET_KEY")
        or "dev-key-change-in-production"
    )

    # Session configuration
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)

    # JSON configuration
    JSON_SORT_KEYS = False
    JSONIFY_PRETTYPRINT_REGULAR = True

    # File paths - use env vars with sensible defaults
    PROJECT_ROOT = Path(os.environ.get("PROJECT_ROOT", Path(__file__).parent.parent))
    BASE_DIR = PROJECT_ROOT

    # Dashboard specific paths
    DASHBOARD_DIR = PROJECT_ROOT / "dashboard"
    STATE_DIR = PROJECT_ROOT / os.environ.get("DASHBOARD_STATE_DIR", "dashboard/state")
    TASKS_FILE = STATE_DIR / "tasks.json"
    COURSES_FILE = STATE_DIR / "courses.json"

    # Build output paths
    BUILD_DIR = PROJECT_ROOT / os.environ.get("BUILD_DIR", "build")
    SYLLABI_DIR = BUILD_DIR / "syllabi"
    SCHEDULES_DIR = BUILD_DIR / "schedules"

    # Content source paths
    CONTENT_DIR = PROJECT_ROOT / os.environ.get("DATA_DIR", "content")
    TEMPLATE_DIR = PROJECT_ROOT / os.environ.get("TEMPLATE_DIR", "templates")

    # Timezone
    TIMEZONE = "America/Anchorage"

    # Pagination
    TASKS_PER_PAGE = 20

    # Cache configuration
    CACHE_TYPE = "simple"
    CACHE_DEFAULT_TIMEOUT = 300

    # Rate limiting
    RATELIMIT_STORAGE_URL = "memory://"
    RATELIMIT_DEFAULT = "100/hour"

    # CORS settings
    CORS_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:5055"]

    # Logging
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

    # Features
    AUTO_SNAPSHOT = os.environ.get("DASH_AUTO_SNAPSHOT", "true").lower() == "true"
    ENABLE_PROFILING = False

    @staticmethod
    def init_app(app: Any) -> None:
        """Initialize application with this config."""
        # Ensure required directories exist
        Config.STATE_DIR.mkdir(parents=True, exist_ok=True)
        (Config.BASE_DIR / "logs").mkdir(exist_ok=True)

        # Set up logging for the app
        import logging

        logging.basicConfig(
            level=getattr(logging, app.config.get("LOG_LEVEL", "INFO")),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(Config.BASE_DIR / "logs" / "dashboard.log"),
                logging.StreamHandler(),
            ],
        )
        app.logger.info(
            f"Application initialized with {app.config.get('ENV', 'default')} configuration"
        )


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True
    TESTING = False

    # Development server
    HOST = os.environ.get("DASH_HOST", "127.0.0.1")
    PORT = int(os.environ.get("DASH_PORT", 5055))

    # Hot reload
    TEMPLATES_AUTO_RELOAD = True

    # Verbose error pages
    PROPAGATE_EXCEPTIONS = True

    # Development database (if using SQLAlchemy)
    SQLALCHEMY_DATABASE_URI = "sqlite:///dev.db"
    SQLALCHEMY_ECHO = True

    # Disable some security features for development
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False

    @staticmethod
    def init_app(app: Any) -> None:
        Config.init_app(app)

        # Development-specific initialization
        import logging

        logging.basicConfig(level=logging.DEBUG)


class TestingConfig(Config):
    """Testing configuration."""

    DEBUG = True
    TESTING = True

    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False

    # Use in-memory database for tests
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"

    # Disable rate limiting in tests
    RATELIMIT_ENABLED = False

    # Use temporary directory for state files
    import tempfile

    STATE_DIR = Path(tempfile.mkdtemp()) / "state"
    TASKS_FILE = STATE_DIR / "tasks.json"
    COURSES_FILE = STATE_DIR / "courses.json"

    # Disable auto snapshot in tests
    AUTO_SNAPSHOT = False

    # Fast password hashing for tests
    BCRYPT_LOG_ROUNDS = 4

    @staticmethod
    def init_app(app: Any) -> None:
        Config.init_app(app)


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False
    TESTING = False

    # Security headers
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Strict"

    # HTTPS enforcement
    PREFERRED_URL_SCHEME = "https"

    # Production database
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL") or "postgresql://user:pass@localhost/dashboard"
    )

    # Connection pool
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 10,
        "pool_recycle": 3600,
        "pool_pre_ping": True,
    }

    # Cache configuration (Redis in production)
    CACHE_TYPE = "redis"
    CACHE_REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

    # Rate limiting with Redis
    RATELIMIT_STORAGE_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/1")

    # Stricter rate limits in production
    RATELIMIT_DEFAULT = "50/hour"

    # CORS - restrict in production
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "").split(",")

    # Enable profiling if needed
    ENABLE_PROFILING = os.environ.get("ENABLE_PROFILING", "false").lower() == "true"

    @staticmethod
    def init_app(app: Any) -> None:
        Config.init_app(app)

        # Production logging
        import logging
        from logging.handlers import RotatingFileHandler

        if not app.debug:
            file_handler = RotatingFileHandler(
                "logs/dashboard.log", maxBytes=10240000, backupCount=10
            )
            file_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
                )
            )
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)

            app.logger.setLevel(logging.INFO)
            app.logger.info("Dashboard startup")


# Configuration dictionary
config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}


def get_config(config_name: str | None = None) -> type[Config]:
    """Get configuration class by name."""
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")
    return config.get(config_name, DevelopmentConfig)
