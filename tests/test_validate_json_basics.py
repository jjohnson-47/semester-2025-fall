"""Basic tests for JSON validation utilities.

These tests focus on file/dir handling and do not rely on
project schemas being present. They skip gracefully if
`jsonschema` is not installed in the current environment.
"""

import json
from pathlib import Path

import pytest

# Skip the module-level import if jsonschema isn't available
pytest.importorskip("jsonschema")

from scripts.validate_json import JSONValidator


def test_validate_file_invalid_json_returns_false(tmp_path: Path) -> None:
    """An invalid JSON file should return False and record an error."""
    bad_file = tmp_path / "broken.json"
    bad_file.write_text("{ not: valid }")

    validator = JSONValidator(schema_dir="scripts/utils/schema")
    ok = validator.validate_file(bad_file)

    assert ok is False
    assert any(str(bad_file) in f for f, _ in validator.errors)


def test_validate_file_valid_json_without_schema_returns_true(tmp_path: Path) -> None:
    """A valid JSON file with no schema specified should be accepted."""
    good_file = tmp_path / "ok.json"
    # Write a simple, valid JSON object
    good_file.write_text(json.dumps({"key": "value"}))

    validator = JSONValidator(schema_dir="scripts/utils/schema")
    ok = validator.validate_file(good_file)

    assert ok is True
    assert validator.errors == []


def test_validate_directory_missing_dir_adds_warning(tmp_path: Path) -> None:
    """Missing directory should yield zero validated files and a warning entry."""
    missing_dir = tmp_path / "does_not_exist"
    validator = JSONValidator(schema_dir="scripts/utils/schema")

    count = validator.validate_directory(missing_dir)

    assert count == 0
    assert any(str(missing_dir) == f for f, _ in validator.warnings)
