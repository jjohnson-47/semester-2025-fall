#!/usr/bin/env bash
# Flask documentation sync script - Downloads latest stable Flask docs
# Usage: bash get-flask-docs.sh [DEST_DIR]
# Default: ./docs/flask-reference
set -euo pipefail

BASE_URL="https://flask.palletsprojects.com/en/stable"
DEST_ROOT="${1:-./docs/flask-reference}"

# Essential Flask documentation sections for optimal development
SECTIONS=(
  "/index.html"
  "/installation/"
  "/quickstart/"
  "/tutorial/"
  "/config/"
  "/logging/"
  "/testing/"
  "/errorhandling/"
  "/debugging/"
  "/cli/"
  "/server/"
  "/appcontext/"
  "/reqcontext/"
  "/blueprints/"
  "/patterns/"
  "/security/"
  "/deploying/"
  "/async/"
  "/lifecycle/"
  "/templating/"
  "/api/"
)

# Create destination directory
mkdir -p "$DEST_ROOT"

# Check for wget
if ! command -v wget >/dev/null 2>&1; then
  echo "Error: wget is required but not installed"
  echo "Install with: sudo dnf install wget"
  exit 1
fi

# Wget configuration for offline documentation
WGET_FLAGS=(
  --no-verbose
  --convert-links
  --page-requisites
  --adjust-extension
  --timeout=15
  --tries=3
  --no-clobber
  --recursive
  --level=2
  --no-parent
  --domains=flask.palletsprojects.com
  --directory-prefix="$DEST_ROOT"
)

echo "📚 Downloading Flask stable documentation..."
echo "   Source: $BASE_URL"
echo "   Destination: $DEST_ROOT"

# Download each section
for section in "${SECTIONS[@]}"; do
  echo "   → Fetching $section"
  wget "${WGET_FLAGS[@]}" "${BASE_URL}${section}" 2>/dev/null || true
done

# Create documentation index
cat > "${DEST_ROOT}/INDEX.md" << 'EOF'
# Flask Documentation Reference

## Documentation Version
- **Source**: Flask stable (3.x)
- **Retrieved**: $(date -u +'%Y-%m-%d %H:%M:%S UTC')
- **Location**: ./docs/flask-reference

## Quick Links

### Getting Started
- [Installation](flask.palletsprojects.com/en/stable/installation/index.html)
- [Quickstart](flask.palletsprojects.com/en/stable/quickstart/index.html)
- [Tutorial](flask.palletsprojects.com/en/stable/tutorial/index.html)

### Core Concepts
- [Configuration](flask.palletsprojects.com/en/stable/config/index.html)
- [Application Context](flask.palletsprojects.com/en/stable/appcontext/index.html)
- [Request Context](flask.palletsprojects.com/en/stable/reqcontext/index.html)
- [Blueprints](flask.palletsprojects.com/en/stable/blueprints/index.html)

### Development
- [Testing](flask.palletsprojects.com/en/stable/testing/index.html)
- [Error Handling](flask.palletsprojects.com/en/stable/errorhandling/index.html)
- [Debugging](flask.palletsprojects.com/en/stable/debugging/index.html)
- [CLI](flask.palletsprojects.com/en/stable/cli/index.html)

### Production
- [Security](flask.palletsprojects.com/en/stable/security/index.html)
- [Deploying](flask.palletsprojects.com/en/stable/deploying/index.html)
- [Logging](flask.palletsprojects.com/en/stable/logging/index.html)

### Advanced
- [Async Support](flask.palletsprojects.com/en/stable/async/index.html)
- [Patterns](flask.palletsprojects.com/en/stable/patterns/index.html)
- [API Reference](flask.palletsprojects.com/en/stable/api/index.html)

## Usage
Open `flask.palletsprojects.com/en/stable/index.html` in your browser for offline access.
EOF

# Update date in index
sed -i "s/\$(date -u +'%Y-%m-%d %H:%M:%S UTC')/$(date -u +'%Y-%m-%d %H:%M:%S UTC')/" "${DEST_ROOT}/INDEX.md"

echo "✅ Flask documentation downloaded successfully!"
echo "   View offline: ${DEST_ROOT}/flask.palletsprojects.com/en/stable/index.html"
echo "   Index: ${DEST_ROOT}/INDEX.md"