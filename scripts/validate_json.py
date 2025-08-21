#!/usr/bin/env python3
"""
Validate all JSON files against their schemas.
Fast-fail validation to catch errors early.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import argparse

from jsonschema import validate, ValidationError, Draft7Validator


class JSONValidator:
    """Validates JSON files against schemas."""
    
    def __init__(self, schema_dir: str = "scripts/utils/schema"):
        self.schema_dir = Path(schema_dir)
        self.schemas = self._load_schemas()
        self.errors: List[Tuple[str, str]] = []
        self.warnings: List[Tuple[str, str]] = []
    
    def _load_schemas(self) -> Dict[str, dict]:
        """Load all JSON schemas."""
        schemas = {}
        
        if not self.schema_dir.exists():
            print(f"Warning: Schema directory not found: {self.schema_dir}")
            return schemas
        
        for schema_file in self.schema_dir.glob("*.schema.json"):
            with open(schema_file, 'r', encoding='utf-8') as f:
                key = schema_file.stem.replace('.schema', '')
                schemas[key] = json.load(f)
                print(f"  Loaded schema: {key}")
        
        return schemas
    
    def validate_file(self, file_path: Path, schema_key: Optional[str] = None) -> bool:
        """Validate a single JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
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
    
    def validate_directory(self, directory: Path, schema_key: Optional[str] = None) -> int:
        """Validate all JSON files in a directory."""
        if not directory.exists():
            self.warnings.append((str(directory), "Directory not found"))
            return 0
        
        count = 0
        for json_file in directory.glob("*.json"):
            if self.validate_file(json_file, schema_key):
                count += 1
            
        return count
    
    def validate_project(self) -> bool:
        """Validate all JSON files in the project."""
        print("\n=== JSON Validation ===\n")
        
        validations = [
            ("variables", "variables"),
            ("global", "variables"),
            ("tables", "tables"),
            ("profiles", "variables"),
            ("content/courses/MATH221", "course"),
            ("content/courses/MATH251", "course"),
            ("content/courses/STAT253", "course"),
        ]
        
        total_valid = 0
        total_files = 0
        
        for directory, schema_key in validations:
            dir_path = Path(directory)
            if dir_path.exists():
                file_count = len(list(dir_path.glob("*.json")))
                valid_count = self.validate_directory(dir_path, schema_key)
                total_files += file_count
                total_valid += valid_count
                
                if valid_count == file_count:
                    print(f"✓ {directory}: {valid_count}/{file_count} valid")
                else:
                    print(f"✗ {directory}: {valid_count}/{file_count} valid")
        
        # Print summary
        self._print_summary(total_valid, total_files)
        
        return len(self.errors) == 0
    
    def _print_summary(self, valid: int, total: int) -> None:
        """Print validation summary."""
        print("\n" + "="*50)
        
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
    parser = argparse.ArgumentParser(description='Validate JSON files')
    parser.add_argument('--strict', action='store_true', help='Strict validation mode')
    parser.add_argument('--schema-dir', default='scripts/utils/schema', help='Schema directory')
    parser.add_argument('--quiet', action='store_true', help='Quiet mode')
    
    args = parser.parse_args()
    
    validator = JSONValidator(schema_dir=args.schema_dir)
    
    if validator.validate_project():
        sys.exit(0)
    else:
        if args.strict:
            sys.exit(1)
        else:
            # In non-strict mode, just warn
            console.print("[yellow]Validation issues found but continuing (non-strict mode)[/yellow]")
            sys.exit(0)


if __name__ == '__main__':
    main()