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
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


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
            console.print(f"[yellow]Warning: Schema directory not found: {self.schema_dir}[/yellow]")
            return schemas
        
        for schema_file in self.schema_dir.glob("*.schema.json"):
            with open(schema_file, 'r', encoding='utf-8') as f:
                key = schema_file.stem.replace('.schema', '')
                schemas[key] = json.load(f)
                console.print(f"[dim]Loaded schema: {key}[/dim]")
        
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
        console.print(Panel("[bold blue]JSON Validation[/bold blue]", expand=False))
        
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
                    console.print(f"✓ {directory}: [green]{valid_count}/{file_count} valid[/green]")
                else:
                    console.print(f"✗ {directory}: [red]{valid_count}/{file_count} valid[/red]")
        
        # Print summary
        self._print_summary(total_valid, total_files)
        
        return len(self.errors) == 0
    
    def _print_summary(self, valid: int, total: int) -> None:
        """Print validation summary."""
        console.print("\n" + "="*50)
        
        if self.errors:
            console.print(f"[bold red]Validation Failed[/bold red]")
            console.print(f"\n[red]Errors ({len(self.errors)}):[/red]")
            for file, error in self.errors[:10]:  # Show first 10 errors
                console.print(f"  • {file}")
                console.print(f"    {error}")
            if len(self.errors) > 10:
                console.print(f"  ... and {len(self.errors) - 10} more")
        
        if self.warnings:
            console.print(f"\n[yellow]Warnings ({len(self.warnings)}):[/yellow]")
            for file, warning in self.warnings:
                console.print(f"  • {file}: {warning}")
        
        # Summary table
        table = Table(title="Validation Summary", show_header=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Total Files", str(total))
        table.add_row("Valid Files", f"[green]{valid}[/green]" if valid == total else f"[yellow]{valid}[/yellow]")
        table.add_row("Errors", f"[red]{len(self.errors)}[/red]" if self.errors else "[green]0[/green]")
        table.add_row("Warnings", f"[yellow]{len(self.warnings)}[/yellow]" if self.warnings else "[green]0[/green]")
        
        console.print(table)
        
        if not self.errors:
            console.print("\n[bold green]✓ All JSON files are valid![/bold green]")
        else:
            console.print("\n[bold red]✗ Validation failed. Fix errors before building.[/bold red]")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description='Validate JSON files')
    parser.add_argument('--strict', action='store_true', help='Strict validation mode')
    parser.add_argument('--schema-dir', default='scripts/utils/schema', help='Schema directory')
    parser.add_argument('--quiet', action='store_true', help='Quiet mode')
    
    args = parser.parse_args()
    
    if args.quiet:
        console.quiet = True
    
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