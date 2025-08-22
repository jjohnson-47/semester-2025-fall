#!/usr/bin/env bash
# Quick Flask documentation download - Essential pages only
# Usage: bash get-flask-docs-quick.sh
set -euo pipefail

BASE_URL="https://flask.palletsprojects.com/en/stable"
DEST_ROOT="./docs/flask-reference"

# Create destination directory
mkdir -p "$DEST_ROOT"

# Check for curl (faster than wget for single files)
if ! command -v curl >/dev/null 2>&1; then
  echo "Error: curl is required but not installed"
  echo "Install with: sudo dnf install curl"
  exit 1
fi

echo "📚 Downloading essential Flask documentation pages..."
echo "   Destination: $DEST_ROOT"

# Essential documentation pages (non-recursive)
PAGES=(
  "index.html"
  "quickstart/index.html"
  "tutorial/index.html"
  "patterns/index.html"
  "config/index.html"
  "testing/index.html"
  "errorhandling/index.html"
  "blueprints/index.html"
  "api/index.html"
  "deploying/index.html"
)

# Download each page
for page in "${PAGES[@]}"; do
  echo "   → Downloading $page"
  # Create directory structure
  page_dir=$(dirname "$page")
  mkdir -p "$DEST_ROOT/$page_dir"
  
  # Download with curl (timeout 10s per file)
  curl -sS --max-time 10 \
    -o "$DEST_ROOT/$page" \
    "$BASE_URL/$page" 2>/dev/null || echo "      ⚠ Failed: $page"
done

# Create a local index with links
cat > "$DEST_ROOT/LOCAL_INDEX.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Flask Documentation - Local Index</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
               max-width: 800px; margin: 40px auto; padding: 0 20px; }
        h1 { color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }
        h2 { color: #555; margin-top: 30px; }
        ul { line-height: 1.8; }
        a { color: #007bff; text-decoration: none; }
        a:hover { text-decoration: underline; }
        .note { background: #f8f9fa; padding: 15px; border-left: 4px solid #007bff; margin: 20px 0; }
    </style>
</head>
<body>
    <h1>Flask Documentation - Local Reference</h1>
    
    <div class="note">
        <strong>Note:</strong> This is a local subset of Flask documentation for offline reference.
        For complete documentation, visit <a href="https://flask.palletsprojects.com">flask.palletsprojects.com</a>
    </div>
    
    <h2>Quick Start</h2>
    <ul>
        <li><a href="index.html">Flask Home</a></li>
        <li><a href="quickstart/index.html">Quickstart Guide</a></li>
        <li><a href="tutorial/index.html">Tutorial</a></li>
    </ul>
    
    <h2>Core Topics</h2>
    <ul>
        <li><a href="config/index.html">Configuration Handling</a></li>
        <li><a href="blueprints/index.html">Blueprints</a></li>
        <li><a href="patterns/index.html">Patterns & Best Practices</a></li>
        <li><a href="api/index.html">API Reference</a></li>
    </ul>
    
    <h2>Development</h2>
    <ul>
        <li><a href="testing/index.html">Testing Flask Applications</a></li>
        <li><a href="errorhandling/index.html">Error Handling</a></li>
    </ul>
    
    <h2>Production</h2>
    <ul>
        <li><a href="deploying/index.html">Deploying to Production</a></li>
    </ul>
    
    <hr style="margin-top: 50px; border: none; border-top: 1px solid #ddd;">
    <p style="color: #777; font-size: 14px;">
        Downloaded: $(date '+%Y-%m-%d %H:%M:%S')<br>
        Source: Flask stable documentation (3.x)
    </p>
</body>
</html>
EOF

# Create README for the documentation
cat > "$DEST_ROOT/README.md" << EOF
# Flask Documentation Reference

## Overview
This directory contains essential Flask documentation pages for offline reference.

## Contents
- Core Flask documentation pages
- Quick reference guides
- API documentation
- Best practices and patterns

## Viewing
Open \`LOCAL_INDEX.html\` in your browser for a navigation index.

## Source
Downloaded from: https://flask.palletsprojects.com/en/stable/
Date: $(date '+%Y-%m-%d %H:%M:%S')
Version: Flask 3.x (stable)

## Note
This is a subset of the full documentation. For complete docs, visit the official site.
EOF

echo "✅ Essential Flask documentation downloaded!"
echo "   View index: $DEST_ROOT/LOCAL_INDEX.html"
echo "   Total pages: ${#PAGES[@]}"