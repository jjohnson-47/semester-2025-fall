#!/usr/bin/env python3
"""Additional tests for export functionality."""

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


def test_export_with_filters(client):
    """Test export endpoints with filters."""
    # CSV export with course filter
    resp = client.get("/api/export/csv?course=MATH221")
    assert resp.status_code == 200
    assert resp.mimetype == "text/csv"

    # JSON export with status filter
    resp = client.get("/api/export/json?status=todo")
    assert resp.status_code == 200
    assert resp.mimetype == "application/json"

    # ICS export with course filter
    resp = client.get("/api/export/ics?course=MATH221")
    assert resp.status_code == 200
    assert resp.mimetype == "text/calendar"
