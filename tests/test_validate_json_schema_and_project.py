"""Extended tests for JSON validation.

Covers schema-based validation, mixed directory handling, and a
`validate_project` run with injected directories for isolation.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("jsonschema")

from scripts.validate_json import JSONValidator  # noqa: E402


def _write_schema(schema_dir: Path, name: str, schema: dict) -> Path:
    """Helper to write a schema file `<name>.schema.json`."""
    schema_dir.mkdir(parents=True, exist_ok=True)
    path = schema_dir / f"{name}.schema.json"
    path.write_text(json.dumps(schema))
    return path


def test_validate_file_with_schema_success_and_failure(tmp_path: Path) -> None:
    """Validate a file against an injected schema (pass and fail)."""
    # Arrange: schema requiring a string `name` property
    schema_dir = tmp_path / "schemas"
    _write_schema(
        schema_dir,
        "sample",
        {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
            "additionalProperties": False,
        },
    )

    validator = JSONValidator(schema_dir=str(schema_dir))

    valid_file = tmp_path / "ok.json"
    invalid_file = tmp_path / "bad.json"
    valid_file.write_text(json.dumps({"name": "Ada"}))
    invalid_file.write_text(json.dumps({"name": 123, "extra": True}))

    assert validator.validate_file(valid_file, schema_key="sample") is True
    assert validator.validate_file(invalid_file, schema_key="sample") is False
    assert any(str(invalid_file) in f and "Schema validation" in msg for f, msg in validator.errors)


def test_validate_directory_counts_mixed_valid_invalid(tmp_path: Path) -> None:
    """Directory validation counts only valid JSON files, records errors for invalid JSON."""
    json_dir = tmp_path / "data"
    json_dir.mkdir(parents=True, exist_ok=True)

    good = json_dir / "good.json"
    bad = json_dir / "bad.json"
    good.write_text(json.dumps({"k": 1}))
    bad.write_text("{ not: valid }")

    validator = JSONValidator(schema_dir=str(tmp_path / "no_schemas"))
    count = validator.validate_directory(json_dir)

    assert count == 1
    assert any(str(bad) in f and "JSON parse error" in msg for f, msg in validator.errors)


def test_validate_project_with_injected_validations(tmp_path: Path) -> None:
    """Smoke-test `validate_project` with injected directories.

    One directory exists with valid JSON, and one is missing. Expect a
    successful validation return (no errors) and one warning.
    """
    existing_dir = tmp_path / "present"
    existing_dir.mkdir(parents=True, exist_ok=True)
    (existing_dir / "a.json").write_text(json.dumps({"ok": True}))

    missing_dir = tmp_path / "absent"

    validations: list[tuple[str, str]] = [(str(existing_dir), ""), (str(missing_dir), "")]
    validator = JSONValidator(schema_dir=str(tmp_path / "schemas"), validations=validations)

    ok = validator.validate_project()

    assert ok is True
    assert validator.errors == []
    assert any(
        str(missing_dir) == f and "Directory not found" in msg for f, msg in validator.warnings
    )
