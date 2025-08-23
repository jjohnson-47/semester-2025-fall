#!/usr/bin/env python3
"""Test statistics endpoints."""

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


def test_stats_endpoints(client):
    """Test statistics endpoints."""
    # Get general stats
    resp = client.get("/api/stats")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "total" in data
    assert "completed" in data
    assert "in_progress" in data
    assert "todo" in data
    assert "completion_rate" in data

    # Get course-specific stats
    resp = client.get("/api/stats/courses/MATH221")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "course" in data
    assert data["course"] == "MATH221"

    # Get stats for non-existent course
    resp = client.get("/api/stats/courses/INVALID")
    assert resp.status_code == 404
