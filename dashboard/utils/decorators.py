#!/usr/bin/env python3
"""
Custom decorators for Flask routes.
"""

from functools import wraps

from flask import current_app, jsonify, request


def validate_json(f):
    """
    Decorator to validate JSON request body.
    Returns 400 if request doesn't contain valid JSON.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400

        try:
            request.get_json()
        except Exception as e:
            current_app.logger.error(f"Invalid JSON: {e}")
            return jsonify({"error": "Invalid JSON in request body"}), 400

        return f(*args, **kwargs)

    return decorated_function


def require_api_key(f):
    """
    Decorator to require API key for access.
    Checks for X-API-Key header.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get("X-API-Key")

        if not api_key:
            return jsonify({"error": "API key required"}), 401

        # In production, validate against stored keys
        valid_key = current_app.config.get("API_KEY")
        if valid_key and api_key != valid_key:
            return jsonify({"error": "Invalid API key"}), 401

        return f(*args, **kwargs)

    return decorated_function


def paginate(default_per_page=20, max_per_page=100):
    """
    Decorator to add pagination parameters to routes.
    Adds 'page' and 'per_page' to kwargs.
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            page = request.args.get("page", 1, type=int)
            per_page = request.args.get("per_page", default_per_page, type=int)

            # Enforce limits
            page = max(1, page)
            per_page = min(max_per_page, max(1, per_page))

            kwargs["page"] = page
            kwargs["per_page"] = per_page

            return f(*args, **kwargs)

        return decorated_function

    return decorator
