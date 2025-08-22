#!/usr/bin/env bash
# Setup development environment for Fall 2025 Dashboard
# This script configures pre-commit hooks and development tools

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Fall 2025 Dashboard Development Setup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check for UV
if ! command -v uv &> /dev/null; then
    echo -e "${RED}❌ UV is not installed${NC}"
    echo "Please install UV first: https://github.com/astral-sh/uv"
    exit 1
fi

echo -e "${GREEN}✓ UV found: $(uv --version)${NC}"

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
REQUIRED_VERSION="3.13"
if [[ ! "$PYTHON_VERSION" == "$REQUIRED_VERSION"* ]]; then
    echo -e "${YELLOW}⚠ Python $PYTHON_VERSION found, but $REQUIRED_VERSION.x is recommended${NC}"
    echo "Installing Python $REQUIRED_VERSION with UV..."
    uv python install 3.13.6
    uv python pin 3.13.6
fi

# Install all dependencies including dev tools
echo -e "${BLUE}Installing dependencies...${NC}"
uv sync --all-extras

# Install pre-commit
echo -e "${BLUE}Installing pre-commit hooks...${NC}"
if ! command -v pre-commit &> /dev/null; then
    echo "Installing pre-commit..."
    uv pip install pre-commit
fi

# Install pre-commit hooks
pre-commit install
pre-commit install --hook-type commit-msg
pre-commit install --hook-type pre-push

echo -e "${GREEN}✓ Pre-commit hooks installed${NC}"

# Run initial validation
echo -e "${BLUE}Running initial validation...${NC}"

# Validate JSON
echo "  Validating JSON files..."
if uv run python scripts/validate_json.py; then
    echo -e "${GREEN}  ✓ JSON validation passed${NC}"
else
    echo -e "${YELLOW}  ⚠ JSON validation failed - please fix before committing${NC}"
fi

# Format code
echo "  Formatting code with Ruff..."
uv run ruff format .
uv run ruff check . --fix --unsafe-fixes
echo -e "${GREEN}  ✓ Code formatted${NC}"

# Check types
echo "  Checking types with MyPy..."
if uv run mypy dashboard/ scripts/ --ignore-missing-imports; then
    echo -e "${GREEN}  ✓ Type checking passed${NC}"
else
    echo -e "${YELLOW}  ⚠ Type checking has warnings${NC}"
fi

# Create state directories if needed
echo -e "${BLUE}Setting up dashboard directories...${NC}"
mkdir -p dashboard/state
mkdir -p dashboard/templates_src
mkdir -p build/{syllabi,schedules,blackboard,weekly,dashboard}
echo -e "${GREEN}✓ Directories created${NC}"

# Git configuration recommendations
echo ""
echo -e "${BLUE}Recommended Git Configuration:${NC}"
echo -e "${YELLOW}Run these commands to optimize your Git workflow:${NC}"
echo ""
echo "  # Enable auto-correction for common typos"
echo "  git config help.autocorrect 10"
echo ""
echo "  # Set up helpful aliases"
echo "  git config alias.st 'status -sb'"
echo "  git config alias.co checkout"
echo "  git config alias.br branch"
echo "  git config alias.ci commit"
echo "  git config alias.unstage 'reset HEAD --'"
echo "  git config alias.last 'log -1 HEAD'"
echo "  git config alias.visual '!gitk'"
echo ""

# Available make commands
echo -e "${BLUE}Available Make Commands:${NC}"
echo "  make help       - Show all available commands"
echo "  make validate   - Validate JSON files"
echo "  make test       - Run test suite"
echo "  make format     - Format Python code"
echo "  make dash       - Start dashboard server"
echo "  make all        - Build everything"
echo ""

# Development workflow
echo -e "${BLUE}Development Workflow:${NC}"
echo "1. Create feature branch: git checkout -b feature/your-feature"
echo "2. Make changes"
echo "3. Code will be auto-formatted on commit (pre-commit hooks)"
echo "4. Run tests: make test"
echo "5. Commit changes: git commit -m 'feat: your feature'"
echo "6. Push and create PR: git push origin feature/your-feature"
echo ""

# Check if running in CI
if [ -n "${CI:-}" ]; then
    echo -e "${BLUE}Running in CI environment - skipping interactive setup${NC}"
else
    # Offer to run pre-commit on all files
    echo -e "${YELLOW}Would you like to run pre-commit checks on all files now? (y/n)${NC}"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}Running pre-commit on all files...${NC}"
        pre-commit run --all-files || true
        echo -e "${GREEN}✓ Pre-commit checks complete${NC}"
    fi
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Development environment ready!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "  1. Run 'make dash' to start the dashboard"
echo "  2. Run 'make test' to run tests"
echo "  3. Start coding! Pre-commit will handle formatting"
echo ""