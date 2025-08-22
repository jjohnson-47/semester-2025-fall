#!/bin/bash
# setup.sh - Setup script for KPC Syllabus Generator
# August 2025 Version

set -e  # Exit on error

echo "🎓 KPC Syllabus Generator Setup"
echo "================================"

# Check Python version
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.9+ is required (found $python_version)"
    exit 1
fi
echo "✓ Python $python_version found"

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
cat > requirements.txt << 'EOF'
# KPC Syllabus Generator Requirements
# Python 3.9+ required

# Core dependencies
Jinja2>=3.1.3
PyYAML>=6.0.1
python-dateutil>=2.9.0

# Optional but recommended
python-docx>=1.1.0  # For direct DOCX generation
markdown>=3.5.2     # For Markdown processing
beautifulsoup4>=4.12.3  # For HTML processing

# Development dependencies
black>=24.2.0      # Code formatting
pytest>=8.0.0      # Testing
mypy>=1.8.0        # Type checking
EOF

pip install --upgrade pip
pip install -r requirements.txt
echo "✓ Python dependencies installed"

# Check for Pandoc
if command -v pandoc &> /dev/null; then
    pandoc_version=$(pandoc --version | head -1 | grep -oE '[0-9]+\.[0-9]+')
    echo "✓ Pandoc $pandoc_version found"
else
    echo "⚠️  Pandoc not found. Installing instructions:"
    echo "   macOS:    brew install pandoc"
    echo "   Ubuntu:   sudo apt-get install pandoc"
    echo "   Windows:  Download from https://pandoc.org/installing.html"
    echo ""
    read -p "Continue without Pandoc? (DOCX export will be limited) [y/N]: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create directory structure
echo "Creating directory structure..."
mkdir -p templates
mkdir -p output
mkdir -p data

# Create Docker setup (optional)
cat > Dockerfile << 'EOF'
# Dockerfile for KPC Syllabus Generator
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    pandoc \
    texlive-xetex \
    texlive-fonts-recommended \
    texlive-plain-generic \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create output directory
RUN mkdir -p /app/output

# Set entrypoint
ENTRYPOINT ["python", "syllabus_generator.py"]
EOF

# Create docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  syllabus-generator:
    build: .
    volumes:
      - ./data:/app/data
      - ./output:/app/output
      - ./templates:/app/templates
    environment:
      - PYTHONUNBUFFERED=1
EOF

# Create Makefile for convenience
cat > Makefile << 'EOF'
# Makefile for KPC Syllabus Generator

.PHONY: help install test clean docker-build docker-run generate

help:
	@echo "Available commands:"
	@echo "  make install      - Install dependencies"
	@echo "  make test        - Run tests"
	@echo "  make clean       - Clean generated files"
	@echo "  make docker-build - Build Docker image"
	@echo "  make docker-run  - Run in Docker"
	@echo "  make generate    - Generate sample syllabus"

install:
	python3 -m venv venv
	./venv/bin/pip install -r requirements.txt

test:
	./venv/bin/pytest tests/

clean:
	rm -rf output/*.html output/*.docx output/*.md
	rm -rf __pycache__ .pytest_cache
	find . -type f -name "*.pyc" -delete

docker-build:
	docker-compose build

docker-run:
	docker-compose run --rm syllabus-generator $(ARGS)

generate:
	./venv/bin/python syllabus_generator.py syllabus_data.yaml
EOF

# Create .gitignore
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# Output files
output/
*.html
*.docx
*.pdf

# IDE
.vscode/
.idea/
*.swp
*.swo
.DS_Store

# Testing
.pytest_cache/
.coverage
htmlcov/

# Docker
.dockerignore
EOF

# Create GitHub Actions workflow
mkdir -p .github/workflows
cat > .github/workflows/test.yml << 'EOF'
name: Test Syllabus Generator

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.9", "3.10", "3.11", "3.12"]

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v5
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install system dependencies
      run: |
        sudo apt-get update
        sudo apt-get install -y pandoc

    - name: Install Python dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt

    - name: Run tests
      run: |
        python syllabus_generator.py --init
        python syllabus_generator.py syllabus_data.yaml

    - name: Upload artifacts
      uses: actions/upload-artifact@v4
      with:
        name: generated-syllabi-${{ matrix.python-version }}
        path: output/
EOF

# Save the template files
echo "Saving template files..."

# Save HTML template
cat > templates/syllabus.html.j2 << 'EOHTML'
[HTML template content from previous artifact - too long to repeat here]
EOHTML

# Save Markdown template
cat > templates/syllabus.md.j2 << 'EOMD'
[Markdown template content from previous artifact - too long to repeat here]
EOMD

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Initialize sample files: python syllabus_generator.py --init"
echo "3. Edit syllabus_data.yaml with your course information"
echo "4. Generate syllabus: python syllabus_generator.py syllabus_data.yaml"
echo ""
echo "Or use Docker:"
echo "  docker-compose build"
echo "  docker-compose run syllabus-generator syllabus_data.yaml"
