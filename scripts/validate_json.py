#!/usr/bin/env python3
"""
Validate JSON files against schemas with a simple CLI.

This module provides a `JSONValidator` class that supports:
- Validating individual files (`validate_file`)
- Validating all `*.json` files in a directory (`validate_directory`)
- Running a project-wide validation (`validate_project`)

The validator loads JSON Schema files from a directory. Schemas are expected to
be named like `<name>.schema.json` and are referenced via `<name>` as the
`schema_key` in validation methods.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from jsonschema import ValidationError, validate


class JSONValidator:
    """Validates JSON files against JSON Schemas.

    Parameters
    ----------
    schema_dir: str
        Directory containing `*.schema.json` files.
    validations: Optional[List[Tuple[str, str]]]
        Optional list of `(directory, schema_key)` pairs used by
        `validate_project()`. If not provided, a sensible project default is
        used.
    """

    def __init__(
        self,
        schema_dir: str = "scripts/utils/schema",
        validations: list[tuple[str, str]] | None = None,
    ) -> None:
        self.schema_dir = Path(schema_dir)
        self.schemas: dict[str, dict] = self._load_schemas()
        self.errors: list[tuple[str, str]] = []
        self.warnings: list[tuple[str, str]] = []
        # Allow injection for testability while preserving default behavior
        self.validations: list[tuple[str, str]] = validations or [
            ("variables", "variables"),
            ("global", "variables"),
            ("tables", "tables"),
            ("profiles", "variables"),
            ("content/courses/MATH221", "course"),
            ("content/courses/MATH251", "course"),
            ("content/courses/STAT253", "course"),
        ]

    def _load_schemas(self) -> dict[str, dict]:
        """Load all JSON Schemas from `schema_dir`.

        Returns a mapping from schema key (basename without `.schema`) to
        parsed schema dict. If the directory is missing, returns an empty map
        and records a warning during project validation when applicable.
        """
        schemas: dict[str, dict] = {}

        if not self.schema_dir.exists():
            print(f"Warning: Schema directory not found: {self.schema_dir}")
            return schemas

        for schema_file in self.schema_dir.glob("*.schema.json"):
            with open(schema_file, encoding="utf-8") as handle:
                key = schema_file.stem.replace(".schema", "")
                schemas[key] = json.load(handle)
                print(f"  Loaded schema: {key}")

        return schemas

    def validate_file(self, file_path: Path, schema_key: str | None = None) -> bool:
        """Validate a single JSON file.

        Returns True if the file is syntactically valid JSON and (when
        `schema_key` is provided and known) conforms to the corresponding
        schema. Records errors internally on failures.
        """
        try:
            with open(file_path, encoding="utf-8") as handle:
                data = json.load(handle)
        except json.JSONDecodeError as e:
            self.errors.append((str(file_path), f"JSON parse error: {e}"))
            return False
        except Exception as e:
            self.errors.append((str(file_path), f"Read error: {e}"))
            return False

        # Determine which schema to use
        if schema_key and schema_key in self.schemas:
            try:
                validate(instance=data, schema=self.schemas[schema_key])
                return True
            except ValidationError as e:
                self.errors.append((str(file_path), f"Schema validation: {e.message}"))
                return False

        # No schema validation, just check JSON is valid
        return True

    def validate_directory(self, directory: Path, schema_key: str | None = None) -> int:
        """Validate all `*.json` files in a directory.

        Returns the count of files that validated successfully. Adds a warning
        if the directory does not exist.
        """
        if not directory.exists():
            self.warnings.append((str(directory), "Directory not found"))
            return 0

        count = 0
        for json_file in directory.glob("*.json"):
            if self.validate_file(json_file, schema_key):
                count += 1

        return count

    def validate_project(self) -> bool:
        """Validate all JSON files across configured directories.

        Uses `self.validations` to determine `(directory, schema_key)` pairs.
        Prints a short summary and returns True when no errors were recorded.
        """
        print("\n=== JSON Validation ===\n")
        validations = self.validations

        total_valid = 0
        total_files = 0

        for directory, schema_key in validations:
            dir_path = Path(directory)
            file_count = len(list(dir_path.glob("*.json"))) if dir_path.exists() else 0
            valid_count = self.validate_directory(dir_path, schema_key)
            total_files += file_count
            total_valid += valid_count

            status = "✓" if valid_count == file_count else "✗"
            print(f"{status} {directory}: {valid_count}/{file_count} valid")

        # Print summary
        self._print_summary(total_valid, total_files)

        return len(self.errors) == 0

    def _print_summary(self, valid: int, total: int) -> None:
        """Print validation summary."""
        print("\n" + "=" * 50)

        if self.errors:
            print("Validation Failed")
            print(f"\nErrors ({len(self.errors)}):")
            for file, error in self.errors[:10]:  # Show first 10 errors
                print(f"  • {file}")
                print(f"    {error}")
            if len(self.errors) > 10:
                print(f"  ... and {len(self.errors) - 10} more")

        if self.warnings:
            print(f"\nWarnings ({len(self.warnings)}):")
            for file, warning in self.warnings:
                print(f"  • {file}: {warning}")

        # Summary
        print("\nValidation Summary:")
        print(f"  Total Files: {total}")
        print(f"  Valid Files: {valid}")
        print(f"  Errors: {len(self.errors)}")
        print(f"  Warnings: {len(self.warnings)}")

        if not self.errors:
            print("\n✓ All JSON files are valid!")
        else:
            print("\n✗ Validation failed. Fix errors before building.")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Validate JSON files")
    parser.add_argument("--strict", action="store_true", help="Strict validation mode")
    parser.add_argument("--schema-dir", default="scripts/utils/schema", help="Schema directory")
    parser.add_argument("--quiet", action="store_true", help="Quiet mode")

    args = parser.parse_args()

    validator = JSONValidator(schema_dir=args.schema_dir)

    if validator.validate_project():
        sys.exit(0)
    else:
        if args.strict:
            sys.exit(1)
        else:
            # In non-strict mode, just warn using standard output
            print("Validation issues found but continuing (non-strict mode)")
            sys.exit(0)


if __name__ == "__main__":
    main()
