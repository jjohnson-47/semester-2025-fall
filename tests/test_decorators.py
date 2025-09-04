#!/usr/bin/env python3
"""
Unit tests for dashboard.utils.decorators.validate_json.
"""

from __future__ import annotations

from flask import Flask, jsonify

from dashboard.utils.decorators import validate_json


def make_app() -> Flask:
  app = Flask(__name__)

  @app.route('/ok', methods=['POST'])
  @validate_json
  def ok():
    return jsonify({"ok": True}), 200

  return app


def test_validate_json_rejects_non_json() -> None:
  app = make_app()
  with app.test_client() as c:
    resp = c.post('/ok', data='not-json', headers={'Content-Type': 'text/plain'})
    assert resp.status_code == 400
    assert b'Content-Type must be application/json' in resp.data


def test_validate_json_rejects_invalid_json() -> None:
  app = make_app()
  with app.test_client() as c:
    resp = c.post('/ok', data='{invalid', headers={'Content-Type': 'application/json'})
    assert resp.status_code == 400


def test_validate_json_accepts_valid_json() -> None:
  app = make_app()
  with app.test_client() as c:
    resp = c.post('/ok', json={'a': 1})
    assert resp.status_code == 200
    assert resp.get_json().get('ok') is True

