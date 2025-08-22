#!/bin/bash
# Pre-commit hook for semester management system
# Validates JSON and checks for common issues

set -e

echo "🔍 Running pre-commit validation..."

# Validate all JSON files
if command -v uv &> /dev/null; then
    uv run python scripts/validate_json.py --strict
else
    python3 scripts/validate_json.py --strict
fi

# Check for sensitive data patterns
echo "🔐 Checking for sensitive data..."
if grep -r "password\|token\|secret\|key" content/ --include="*.json" 2>/dev/null | grep -v "ssh_key\|api_key"; then
    echo "⚠️  Warning: Possible sensitive data found in content files"
    echo "Please review before committing"
fi

# Check for large files
echo "📊 Checking file sizes..."
find build/ -type f -size +1M 2>/dev/null | while read -r file; do
    echo "⚠️  Large file detected: $file"
    echo "Consider adding to .gitignore"
done

# Ensure UV lock is up to date
if [ -f "pyproject.toml" ]; then
    if [ "pyproject.toml" -nt "uv.lock" ]; then
        echo "⚠️  pyproject.toml is newer than uv.lock"
        echo "Run 'uv lock' to update dependencies"
    fi
fi

echo "✅ Pre-commit checks complete!"
