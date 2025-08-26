#!/usr/bin/env python3
"""Schema migrator for course data files.

Handles migration between schema versions, with dry-run capability
and rollback support.
"""

import argparse
import json
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional
import sys

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.schema.versions.v1_1_0 import SchemaValidator, SCHEMA_VERSION


class SchemaMigrator:
    """Migrates course JSON files between schema versions."""
    
    def __init__(self, dry_run: bool = True, backup: bool = True):
        """Initialize migrator.
        
        Args:
            dry_run: If True, don't modify files
            backup: If True, create .bak files before migration
        """
        self.dry_run = dry_run
        self.backup = backup
        self.validator = SchemaValidator()
        self.results: List[Dict[str, Any]] = []
    
    def migrate_file(self, file_path: Path) -> Dict[str, Any]:
        """Migrate a single JSON file to latest schema.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            Migration result dictionary
        """
        result = {
            "file": str(file_path),
            "status": "pending",
            "errors": [],
            "changes": []
        }
        
        try:
            # Read existing data
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Determine document type from path
            doc_type = "course"
            if "schedule" in file_path.name:
                doc_type = "schedule"
            elif "syllabus" in file_path.name:
                doc_type = "syllabus"
            elif "evaluation" in file_path.name:
                doc_type = "evaluation"
            elif "policies" in file_path.name:
                doc_type = "policies"
            
            # Check if already at target version
            if "_meta" in data and data["_meta"].get("version") == SCHEMA_VERSION:
                result["status"] = "already_migrated"
                return result
            
            # Track changes
            had_meta = "_meta" in data
            had_id = "id" in data
            
            # Perform migration
            migrated_data = self.validator.upgrade_document(data, doc_type)
            
            # Track what changed
            if not had_meta:
                result["changes"].append("Added _meta header")
            if not had_id:
                result["changes"].append("Added stable ID")
            
            # Count nested IDs added
            if doc_type == "schedule" and "weeks" in migrated_data:
                weeks_with_ids = sum(1 for w in migrated_data["weeks"] if "id" in w)
                if weeks_with_ids > 0:
                    result["changes"].append(f"Added IDs to {weeks_with_ids} weeks")
            
            # Validate migrated data
            is_valid, errors = self.validator.validate(migrated_data)
            if not is_valid:
                result["status"] = "validation_failed"
                result["errors"] = errors
                return result
            
            # Write back if not dry run
            if not self.dry_run:
                # Backup if requested
                if self.backup:
                    backup_path = file_path.with_suffix(file_path.suffix + '.bak')
                    shutil.copy2(file_path, backup_path)
                    result["changes"].append(f"Created backup: {backup_path.name}")
                
                # Write migrated data
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(migrated_data, f, indent=2)
                
                result["status"] = "migrated"
            else:
                result["status"] = "dry_run_success"
            
        except json.JSONDecodeError as e:
            result["status"] = "error"
            result["errors"].append(f"Invalid JSON: {e}")
        except Exception as e:
            result["status"] = "error"
            result["errors"].append(str(e))
        
        return result
    
    def migrate_directory(self, directory: Path) -> List[Dict[str, Any]]:
        """Migrate all JSON files in a directory.
        
        Args:
            directory: Directory containing JSON files
            
        Returns:
            List of migration results
        """
        results = []
        
        # Find all JSON files
        json_files = list(directory.rglob("*.json"))
        
        print(f"Found {len(json_files)} JSON files to migrate")
        
        for file_path in json_files:
            # Skip backup files
            if file_path.suffix == '.bak':
                continue
            
            # Skip already-migrated files in dry run
            if self.dry_run:
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        if "_meta" in data and data["_meta"].get("version") == SCHEMA_VERSION:
                            print(f"Skipping {file_path.name} (already migrated)")
                            continue
                except:
                    pass
            
            print(f"Migrating {file_path.relative_to(directory)}...")
            result = self.migrate_file(file_path)
            results.append(result)
            
            # Print result
            if result["status"] == "migrated":
                print(f"  ✓ Migrated successfully")
            elif result["status"] == "dry_run_success":
                print(f"  ✓ Would migrate successfully")
                for change in result["changes"]:
                    print(f"    - {change}")
            elif result["status"] == "already_migrated":
                print(f"  ⊙ Already at version {SCHEMA_VERSION}")
            else:
                print(f"  ✗ Failed: {result['status']}")
                for error in result["errors"]:
                    print(f"    - {error}")
        
        self.results = results
        return results
    
    def print_summary(self) -> None:
        """Print migration summary."""
        if not self.results:
            print("\nNo files processed")
            return
        
        # Count by status
        status_counts = {}
        for result in self.results:
            status = result["status"]
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print("\n" + "=" * 50)
        print("Migration Summary")
        print("=" * 50)
        
        for status, count in sorted(status_counts.items()):
            print(f"{status:20s}: {count:3d} files")
        
        print(f"{'Total':20s}: {len(self.results):3d} files")
        
        if self.dry_run:
            print("\n⚠️  DRY RUN - No files were modified")
            print("Run with --apply to perform actual migration")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Migrate course JSON files to latest schema version"
    )
    parser.add_argument(
        "directory",
        type=Path,
        help="Directory containing JSON files to migrate"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually perform migration (default is dry-run)"
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Don't create backup files"
    )
    
    args = parser.parse_args()
    
    if not args.directory.exists():
        print(f"Error: Directory {args.directory} does not exist")
        sys.exit(1)
    
    # Create migrator
    migrator = SchemaMigrator(
        dry_run=not args.apply,
        backup=not args.no_backup
    )
    
    # Run migration
    print(f"Migrating files in {args.directory}")
    print(f"Target schema version: {SCHEMA_VERSION}")
    print(f"Mode: {'APPLY' if args.apply else 'DRY RUN'}")
    print()
    
    migrator.migrate_directory(args.directory)
    migrator.print_summary()


if __name__ == "__main__":
    main()