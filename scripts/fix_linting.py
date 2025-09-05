#!/usr/bin/env python3
"""
Comprehensive linting fix script for the entire codebase.
Systematically addresses all linting and type issues.
"""

import re
import subprocess
import sys
from pathlib import Path

# Issue categories and priorities
ISSUE_CATEGORIES = {
    "critical": [
        "F821",  # Undefined name
        "E402",  # Module import not at top
    ],
    "unused_arguments": [
        "ARG001",  # Unused function argument
        "ARG002",  # Unused method argument  
    ],
    "unused_variables": [
        "F841",  # Local variable assigned but never used
        "B007",  # Loop control variable not used
    ],
    "style": [
        "SIM117",  # Multiple with statements
        "SIM105",  # Use contextlib.suppress
        "RUF003",  # Ambiguous unicode character
        "RUF005",  # Collection literal concatenation
        "UP038",  # Use X | Y in isinstance
    ]
}


class LintingFixer:
    """Systematic linting issue fixer."""
    
    def __init__(self, root_dir: Path = Path(".")):
        self.root_dir = root_dir
        self.fixes_applied = 0
        self.files_modified: set[str] = set()
        
    def get_current_issues(self) -> dict[str, list[tuple[int, str, str]]]:
        """Get all current linting issues grouped by file."""
        cmd = [
            "uv", "run", "--with", "ruff", "ruff", "check",
            "scripts/", "dashboard/", "tests/",
            "--output-format=json"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if not result.stdout:
            return {}
            
        import json
        issues = json.loads(result.stdout)
        
        # Group by file
        by_file: dict[str, list[tuple[int, str, str]]] = {}
        for issue in issues:
            filepath = issue["filename"]
            if filepath not in by_file:
                by_file[filepath] = []
            by_file[filepath].append((
                issue["location"]["row"],
                issue["code"],
                issue["message"]
            ))
            
        return by_file
    
    def fix_undefined_names(self, filepath: Path) -> bool:
        """Fix F821 undefined name errors."""
        content = filepath.read_text()
        modified = False
        
        # Special case for test_golden_validation.py
        if filepath.name == "test_golden_validation.py":
            # The undefined 'course' is likely a missing parameter
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'def test_' in line and 'course' not in line and i + 1 < len(lines) and 'course' in lines[i + 1]:
                    # Add course parameter
                    lines[i] = line.replace('(self)', '(self, course)')
                    modified = True
            
            if modified:
                filepath.write_text('\n'.join(lines))
                self.files_modified.add(str(filepath))
        
        return modified
    
    def fix_unused_arguments(self, filepath: Path) -> bool:
        """Fix ARG001/ARG002 unused argument issues."""
        content = filepath.read_text()
        lines = content.split('\n')
        modified = False
        
        for i, line in enumerate(lines):
            # Skip if already has underscore prefix
            if 'def ' in line and '(' in line:
                # Extract parameters
                match = re.search(r'def \w+\((.*?)\)', line)
                if match:
                    params = match.group(1)
                    # Check each parameter
                    new_params = []
                    changed = False
                    
                    for param in params.split(','):
                        param = param.strip()
                        if not param:
                            continue
                            
                        # Skip self, cls, and already underscored params
                        if param in ('self', 'cls') or param.startswith('_'):
                            new_params.append(param)
                        elif ':' in param:
                            # Has type annotation
                            name, rest = param.split(':', 1)
                            name = name.strip()
                            
                            # Check if this param is reported as unused
                            # For now, prefix with underscore if fixture-like
                            if any(x in name for x in ['tmp', 'mock', 'fixture', 'frozen']):
                                if not name.startswith('_'):
                                    new_params.append(f"_{name}:{rest}")
                                    changed = True
                                else:
                                    new_params.append(param)
                            else:
                                new_params.append(param)
                        else:
                            new_params.append(param)
                    
                    if changed:
                        new_line = line[:match.start(1)] + ', '.join(new_params) + line[match.end(1):]
                        lines[i] = new_line
                        modified = True
        
        if modified:
            filepath.write_text('\n'.join(lines))
            self.files_modified.add(str(filepath))
            
        return modified
    
    def fix_unused_variables(self, filepath: Path) -> bool:
        """Fix F841 unused variable issues."""
        content = filepath.read_text()
        lines = content.split('\n')
        modified = False
        
        for i, line in enumerate(lines):
            # Look for simple assignments that can be prefixed with _
            if '=' in line and not line.strip().startswith('#'):
                # Pattern: variable = something
                match = re.match(r'^(\s*)(\w+)\s*=\s*(.+)$', line)
                if match:
                    indent, var_name, rest = match.groups()
                    
                    # Check if this is likely unused (common patterns)
                    if var_name in ['result', 'response', 'output', 'data', 'ret', 'val']:
                        # Check if used in next few lines
                        used = False
                        for j in range(i + 1, min(i + 5, len(lines))):
                            if var_name in lines[j]:
                                used = True
                                break
                        
                        if not used:
                            lines[i] = f"{indent}_ = {rest}  # Was: {var_name}"
                            modified = True
            
            # Fix loop control variables
            if 'for ' in line and ' in ' in line:
                match = re.match(r'^(\s*)for\s+(\w+)\s+in\s+(.+):$', line)
                if match:
                    indent, var_name, rest = match.groups()
                    # Check if loop var is used in loop body
                    if i + 1 < len(lines):
                        next_indent = len(lines[i + 1]) - len(lines[i + 1].lstrip())
                        loop_indent = len(indent)
                        
                        # Simple check: is var used in immediate next line?
                        if next_indent > loop_indent and var_name not in lines[i + 1]:
                            lines[i] = f"{indent}for _ in {rest}:  # Was: {var_name}"
                            modified = True
        
        if modified:
            filepath.write_text('\n'.join(lines))
            self.files_modified.add(str(filepath))
            
        return modified
    
    def fix_style_issues(self, filepath: Path) -> bool:
        """Fix style issues like nested with statements."""
        content = filepath.read_text()
        modified = False
        
        # Fix RUF003 - ambiguous unicode characters
        # Using raw string to avoid ambiguous unicode issues
        multiplication_sign = '\u00d7'  # Unicode MULTIPLICATION SIGN
        if multiplication_sign in content:
            content = content.replace(multiplication_sign, 'x')
            modified = True
        
        # Fix UP038 - isinstance tuple to union
        content = re.sub(
            r'isinstance\(([^,]+),\s*\(([^)]+)\)\)',
            r'isinstance(\1, \2)',
            content
        )
        
        if modified:
            filepath.write_text(content)
            self.files_modified.add(str(filepath))
            
        return modified
    
    def apply_auto_fixes(self) -> int:
        """Apply automatic ruff fixes."""
        cmd = [
            "uv", "run", "--with", "ruff", "ruff", "check",
            "scripts/", "dashboard/", "tests/",
            "--fix"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Count fixes from output
        if "fixed" in result.stderr:
            match = re.search(r'(\d+) fixed', result.stderr)
            if match:
                return int(match.group(1))
        
        return 0
    
    def fix_all_issues(self):
        """Main method to fix all linting issues."""
        print("=" * 60)
        print("COMPREHENSIVE LINTING FIX")
        print("=" * 60)
        
        # Step 1: Apply automatic fixes
        print("\n1. Applying automatic ruff fixes...")
        auto_fixed = self.apply_auto_fixes()
        print(f"   ✓ Auto-fixed {auto_fixed} issues")
        
        # Step 2: Get remaining issues
        print("\n2. Analyzing remaining issues...")
        issues = self.get_current_issues()
        total_issues = sum(len(v) for v in issues.values())
        print(f"   Found {total_issues} issues in {len(issues)} files")
        
        # Step 3: Fix critical issues
        print("\n3. Fixing critical issues...")
        for filepath, file_issues in issues.items():
            path = Path(filepath)
            
            # Fix undefined names
            has_undefined = any(code == "F821" for _, code, _ in file_issues)
            if has_undefined and self.fix_undefined_names(path):
                print(f"   ✓ Fixed undefined names in {path.name}")
        
        # Step 4: Fix unused arguments
        print("\n4. Fixing unused arguments...")
        for filepath, file_issues in issues.items():
            path = Path(filepath)
            
            has_unused_args = any(code in ["ARG001", "ARG002"] for _, code, _ in file_issues)
            if has_unused_args and self.fix_unused_arguments(path):
                print(f"   ✓ Fixed unused arguments in {path.name}")
        
        # Step 5: Fix unused variables
        print("\n5. Fixing unused variables...")
        for filepath, file_issues in issues.items():
            path = Path(filepath)
            
            has_unused_vars = any(code in ["F841", "B007"] for _, code, _ in file_issues)
            if has_unused_vars and self.fix_unused_variables(path):
                print(f"   ✓ Fixed unused variables in {path.name}")
        
        # Step 6: Fix style issues
        print("\n6. Fixing style issues...")
        for filepath, file_issues in issues.items():
            path = Path(filepath)
            
            has_style = any(code in ["RUF003", "UP038"] for _, code, _ in file_issues)
            if has_style and self.fix_style_issues(path):
                print(f"   ✓ Fixed style issues in {path.name}")
        
        # Step 7: Apply final auto-fixes
        print("\n7. Applying final automatic fixes...")
        final_fixed = self.apply_auto_fixes()
        print(f"   ✓ Auto-fixed {final_fixed} additional issues")
        
        # Step 8: Report
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Files modified: {len(self.files_modified)}")
        print(f"Total fixes applied: {auto_fixed + final_fixed + len(self.files_modified)}")
        
        # Check remaining issues
        final_issues = self.get_current_issues()
        final_count = sum(len(v) for v in final_issues.values())
        print(f"Remaining issues: {final_count}")
        
        if final_count > 0:
            print("\nRemaining issues by type:")
            issue_types = {}
            for file_issues in final_issues.values():
                for _, code, _ in file_issues:
                    issue_types[code] = issue_types.get(code, 0) + 1
            
            for code, count in sorted(issue_types.items(), key=lambda x: -x[1]):
                print(f"  {code}: {count}")


def main():
    """Main entry point."""
    fixer = LintingFixer()
    fixer.fix_all_issues()
    
    # Run tests to ensure nothing broke
    print("\n" + "=" * 60)
    print("VERIFICATION")
    print("=" * 60)
    print("Running quick test to ensure nothing broke...")
    
    result = subprocess.run(
        ["uv", "run", "pytest", "tests/", "-x", "-q", "--tb=no"],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode == 0:
        print("✓ Tests still passing!")
    else:
        print("✗ Some tests failed. Review changes carefully.")
        print(result.stdout[:500])
    
    return 0


if __name__ == "__main__":
    sys.exit(main())