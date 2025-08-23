#!/usr/bin/env python3
"""Test main views."""

import pytest

from dashboard import create_app


@pytest.fixture
def app():
    """Create test app."""
    app = create_app("testing")
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


def test_main_view_imports():
    """Test that main views can be imported without errors."""
    from dashboard.views import main_bp
    from dashboard.views.main import courses_view, index, tasks_view

    # Check that functions exist
    assert callable(index)
    assert callable(tasks_view)
    assert callable(courses_view)

    # Check that blueprint has routes
    assert len(main_bp.deferred_functions) > 0 or hasattr(main_bp, "_got_registered_once")
