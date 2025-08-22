#!/usr/bin/env python3
"""
Unit tests for utility decorators (validate_json, paginate).
"""

from __future__ import annotations

import json

import pytest
from flask import jsonify

from dashboard import create_app
from dashboard.utils.decorators import paginate, validate_json, require_api_key


@pytest.fixture
def app():
    app = create_app("testing")
    app.config["TESTING"] = True

    @app.route("/decorators/echo", methods=["POST"])
    @validate_json
    def echo_json():  # type: ignore
        return jsonify({"ok": True})

    @app.route("/decorators/page", methods=["GET"])
    @paginate(default_per_page=5, max_per_page=10)
    def page_endpoint(page: int, per_page: int):  # type: ignore
        return jsonify({"page": page, "per_page": per_page})

    return app


@pytest.fixture
def client(app):
    return app.test_client()


def test_validate_json_decorator(client):
    # Wrong content-type
    resp = client.post("/decorators/echo", data="{}", headers={"Content-Type": "text/plain"})
    assert resp.status_code == 400

    # Malformed JSON
    resp = client.post("/decorators/echo", data="{bad}", headers={"Content-Type": "application/json"})
    assert resp.status_code == 400

    # OK JSON
    resp = client.post("/decorators/echo", data=json.dumps({}), headers={"Content-Type": "application/json"})
    assert resp.status_code == 200


def test_paginate_decorator(client):
    # Defaults
    resp = client.get("/decorators/page")
    data = resp.get_json()
    assert data["page"] == 1 and data["per_page"] == 5

    # Bounded values
    resp = client.get("/decorators/page?page=2&per_page=1000")
    data = resp.get_json()
    assert data["page"] == 2 and data["per_page"] == 10


def test_require_api_key_decorator():
    app = create_app("testing")
    app.config["TESTING"] = True
    app.config["API_KEY"] = "secret"

    @app.route("/decorators/secure", methods=["GET"])
    @require_api_key
    def secure():  # type: ignore
        return jsonify({"ok": True})

    client = app.test_client()

    # Missing key -> 401
    assert client.get("/decorators/secure").status_code == 401
    # Invalid key -> 401
    assert client.get("/decorators/secure", headers={"X-API-Key": "nope"}).status_code == 401
    # Valid key -> 200
    assert client.get("/decorators/secure", headers={"X-API-Key": "secret"}).status_code == 200
