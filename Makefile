# Fall 2025 Semester Build System
# Generates syllabi, schedules, and Blackboard packages for all courses

.PHONY: all init validate calendar syllabi schedules weekly packages clean help
.DEFAULT_GOAL := help

# Configuration
UV := uv
PYTHON := uv run python
SEMESTER := fall-2025
BUILD_DIR := build
COURSES := MATH221 MATH251 STAT253

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

# Documentation targets
docs: ## Download all project documentation
	@echo "$(BLUE)Downloading project documentation...$(NC)"
	@bash scripts/fetch-all-docs.sh
	@echo "$(GREEN)✓ Documentation downloaded$(NC)"

docs-flask: ## Download Flask documentation only
	@echo "$(BLUE)Downloading Flask documentation...$(NC)"
	@bash scripts/get-flask-docs-quick.sh
	@echo "$(GREEN)✓ Flask documentation downloaded$(NC)"

docs-api: ## Generate API documentation from docstrings
	@echo "$(BLUE)Generating API documentation...$(NC)"
	@$(UV) run --with sphinx,sphinx-rtd-theme,myst-parser sphinx-build -b html docs docs/_build/html
	@echo "$(GREEN)✓ API documentation generated at docs/_build/html$(NC)"

docs-coverage: ## Check documentation coverage
	@echo "$(BLUE)Checking documentation coverage...$(NC)"
	@$(UV) run --with sphinx,sphinx-rtd-theme sphinx-build -b coverage docs docs/_build/coverage
	@cat docs/_build/coverage/python.txt
	@echo "$(GREEN)✓ Documentation coverage report generated$(NC)"

# Help target
help: ## Show this help message
	@echo "$(BLUE)Fall 2025 Semester Build System$(NC)"
	@echo "$(GREEN)Available targets:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Course-specific builds:$(NC)"
	@echo "  $(YELLOW)make course COURSE=MATH221$(NC)  Build specific course materials"

# Initialize environment
init: ## Sync UV dependencies
	@echo "$(BLUE)Initializing environment...$(NC)"
	@$(UV) sync
	@echo "$(GREEN)✓ Dependencies installed$(NC)"
	@$(MAKE) validate

# Validate all JSON files
validate: ## Validate JSON files against schemas
	@echo "$(BLUE)Validating JSON files...$(NC)"
	@$(PYTHON) scripts/validate_json.py
	@echo "$(GREEN)✓ All JSON files valid$(NC)"

# Generate semester calendar
calendar: validate ## Generate semester calendar from variables
	@echo "$(BLUE)Generating semester calendar...$(NC)"
	@$(PYTHON) scripts/utils/semester_calendar.py
	@echo "$(GREEN)✓ Calendar generated$(NC)"

# Build all syllabi
syllabi: calendar ## Generate syllabi for all courses
	@echo "$(BLUE)Building syllabi...$(NC)"
	@mkdir -p $(BUILD_DIR)/syllabi
	@$(PYTHON) scripts/build_syllabi.py
	@echo "$(GREEN)✓ Syllabi generated for: $(COURSES)$(NC)"

# Generate schedules
schedules: calendar ## Generate course schedules
	@echo "$(BLUE)Building schedules...$(NC)"
	@mkdir -p $(BUILD_DIR)/schedules
	@$(PYTHON) scripts/build_schedules.py
	@echo "$(GREEN)✓ Schedules generated$(NC)"

# Generate weekly folders
weekly: calendar ## Create weekly overview pages
	@echo "$(BLUE)Creating weekly folders...$(NC)"
	@mkdir -p $(BUILD_DIR)/weekly
	@$(PYTHON) scripts/weekgen.py
	@echo "$(GREEN)✓ Weekly folders created$(NC)"

# Build Blackboard packages
packages: syllabi schedules weekly ## Create Blackboard import packages
	@echo "$(BLUE)Building Blackboard packages...$(NC)"
	@mkdir -p $(BUILD_DIR)/blackboard
	@$(PYTHON) scripts/build_bb_packages.py
	@echo "$(GREEN)✓ Blackboard packages created$(NC)"

# Build specific course
course: validate ## Build materials for specific course (use COURSE=MATH221)
ifndef COURSE
	@echo "$(RED)Error: COURSE variable not set$(NC)"
	@echo "Usage: make course COURSE=MATH221"
	@exit 1
endif
	@echo "$(BLUE)Building $(COURSE)...$(NC)"
	@mkdir -p $(BUILD_DIR)/{syllabi,schedules,blackboard}
	@$(PYTHON) scripts/build_syllabi.py --course $(COURSE)
	@$(PYTHON) scripts/build_schedules.py --course $(COURSE)
	@$(PYTHON) scripts/build_bb_packages.py --course $(COURSE)
	@echo "$(GREEN)✓ $(COURSE) build complete$(NC)"

# Build everything
all: validate calendar syllabi schedules weekly packages ## Complete build for all courses
	@echo "$(GREEN)════════════════════════════════════$(NC)"
	@echo "$(GREEN)✓ All builds complete!$(NC)"
	@echo "$(GREEN)════════════════════════════════════$(NC)"
	@ls -la $(BUILD_DIR)/

# Clean build artifacts
clean: ## Remove all generated files
	@echo "$(YELLOW)Cleaning build artifacts...$(NC)"
	@rm -rf $(BUILD_DIR)/*
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)✓ Clean complete$(NC)"

# Development targets
.PHONY: dev-server lint format test

dev-server: ## Start development server for preview
	@echo "$(BLUE)Starting preview server...$(NC)"
	@cd $(BUILD_DIR) && uv run python -m http.server 8000

lint: ## Run code linting with Ruff
	@echo "$(BLUE)Running linters...$(NC)"
	@$(UV) run ruff check .
	@$(UV) run mypy dashboard/ scripts/ --ignore-missing-imports
	@echo "$(GREEN)✓ Linting complete$(NC)"

format: ## Format Python code with Ruff
	@echo "$(BLUE)Formatting code...$(NC)"
	@$(UV) run ruff format .
	@$(UV) run ruff check . --fix --unsafe-fixes
	@echo "$(GREEN)✓ Code formatted$(NC)"

test: validate ## Run tests
	@echo "$(BLUE)Running tests...$(NC)"
	@$(UV) run --with pytest pytest tests/

sync-guides: ## Convert course guide Markdown into course JSON (description, prereqs, goals, outcomes)
	@echo "$(BLUE)Syncing course guides into course JSON...$(NC)"
	@$(PYTHON) scripts/utils/sync_course_guides.py --courses MATH221 MATH251 STAT253
	@echo "$(GREEN)✓ Course guides synced$(NC)"

.PHONY: preview
preview: ## Build syllabi/schedules and launch dashboard (one-step workflow)
	@echo "$(BLUE)Preparing syllabi and schedules for dashboard...$(NC)"
	@$(MAKE) sync-guides --no-print-directory
	@$(MAKE) validate --no-print-directory || true
	@$(MAKE) syllabi --no-print-directory
	@$(MAKE) schedules --no-print-directory
	@$(MAKE) weekly --no-print-directory
	@$(MAKE) dash --no-print-directory

# Scaffold course content
scaffold: ## Scaffold content for a course (use COURSE=MATH221)
ifndef COURSE
	@echo "$(RED)Error: COURSE variable not set$(NC)"
	@echo "Usage: make scaffold COURSE=MATH221"
	@exit 1
endif
	@echo "$(BLUE)Scaffolding course $(COURSE)...$(NC)"
	@$(PYTHON) scripts/utils/scaffold_course.py --course $(COURSE)
	@echo "$(GREEN)✓ Scaffold complete$(NC)"

# Installation check
check-deps: ## Check required dependencies
	@echo "$(BLUE)Checking dependencies...$(NC)"
	@which uv > /dev/null && echo "$(GREEN)✓ UV found$(NC)" || echo "$(RED)✗ UV not found$(NC)"
	@which pandoc > /dev/null && echo "$(GREEN)✓ Pandoc found$(NC)" || echo "$(YELLOW)⚠ Pandoc not found (optional for PDF)$(NC)"
	@which git > /dev/null && echo "$(GREEN)✓ Git found$(NC)" || echo "$(RED)✗ Git not found$(NC)"

# Dashboard targets
.PHONY: dash-init dash-gen dash-validate dash dash-open dash-export dash-snapshot dash-reset

dash-init: init ## Initialize dashboard environment
	@echo "$(BLUE)Setting up dashboard environment...$(NC)"
	@$(UV) sync --extra dashboard
	@mkdir -p dashboard/state dashboard/templates_src build/dashboard
	@$(PYTHON) scripts/generate_dashboard_config.py
	@echo "$(GREEN)✓ Dashboard initialized$(NC)"

dash-gen: dash-init ## Generate tasks from templates
	@echo "$(BLUE)Generating tasks from templates...$(NC)"
	@$(PYTHON) dashboard/tools/generate_tasks.py \
		--courses dashboard/state/courses.json \
		--templates dashboard/templates_src \
		--out dashboard/state/tasks.json
	@$(MAKE) dash-validate --no-print-directory
	@$(MAKE) dash-prioritize --no-print-directory
	@echo "$(GREEN)✓ Tasks generated successfully$(NC)"

dash-prioritize: ## Compute smart scores and Now Queue
	@echo "$(BLUE)Reprioritizing tasks...$(NC)"
	@$(PYTHON) dashboard/tools/reprioritize.py \
		--tasks dashboard/state/tasks.json \
		--contracts dashboard/tools/priority_contracts.yaml \
		--semester-first-day 2025-08-25 \
		--write
	@echo "$(GREEN)✓ Reprioritization complete$(NC)"

dash-validate: ## Validate task data integrity
	@echo "$(BLUE)Validating task data...$(NC)"
	@$(PYTHON) dashboard/tools/validate.py
	@echo "$(GREEN)✓ Validation passed$(NC)"

dash: dash-gen ## Run dashboard server
	@echo "$(BLUE)Starting dashboard server on http://127.0.0.1:5055$(NC)"
	@FLASK_APP=dashboard/app.py FLASK_ENV=development \
	DASH_PORT=5055 DASH_HOST=127.0.0.1 \
	$(UV) run flask run --host=127.0.0.1 --port=5055

dash-open: ## Open dashboard in browser
	@xdg-open http://127.0.0.1:5055 2>/dev/null || \
	 open http://127.0.0.1:5055 2>/dev/null || \
	 echo "Please open http://127.0.0.1:5055 in your browser"

dash-export: ## Export dashboard data (ICS, CSV)
	@echo "$(BLUE)Exporting dashboard data...$(NC)"
	@$(PYTHON) dashboard/tools/export.py 2>/dev/null || echo "Export tool not yet implemented"
	@echo "$(GREEN)✓ Export complete$(NC)"

dash-snapshot: ## Create git snapshot of current state
	@git add dashboard/state/tasks.json 2>/dev/null && \
	 git commit -m "dashboard: snapshot $$(date -Iseconds)" 2>/dev/null || \
	 echo "No changes to snapshot"

dash-reset: ## Reset all task statuses for new semester
	@echo "$(BLUE)Resetting all task statuses...$(NC)"
	@$(PYTHON) dashboard/tools/reset.py 2>/dev/null || echo "Reset tool not yet implemented"
	@$(MAKE) dash-snapshot --no-print-directory
	@echo "$(GREEN)✓ All tasks reset to 'todo' status$(NC)"

# CI/CD targets
.PHONY: ci-validate ci-build ci-test ci-lint ci-setup

ci-setup: ## Setup CI environment
	@echo "$(BLUE)Setting up CI environment...$(NC)"
	@uv python install $(PYTHON_VERSION)
	@uv python pin $(PYTHON_VERSION)
	@uv sync --all-extras
	@echo "$(GREEN)✓ CI environment ready$(NC)"

ci-validate: ## CI validation step
	@$(UV) run python scripts/validate_json.py --strict

ci-build: ## CI build step
	@$(UV) run python scripts/build_syllabi.py --ci
	@$(UV) run python scripts/build_schedules.py --ci
	@$(UV) run python scripts/build_bb_packages.py --ci

ci-test: ## CI test step with coverage
	@$(UV) run pytest tests/ -v --cov=dashboard --cov=scripts --cov-report=xml --cov-report=term

ci-lint: ## CI linting and formatting check
	@$(UV) run ruff format --check .
	@$(UV) run ruff check .
	@$(UV) run mypy dashboard/ scripts/ --ignore-missing-imports

# Pre-commit setup
.PHONY: pre-commit-install pre-commit-run

pre-commit-install: ## Install pre-commit hooks
	@echo "$(BLUE)Installing pre-commit hooks...$(NC)"
	@$(UV) pip install pre-commit
	@pre-commit install
	@pre-commit install --hook-type commit-msg
	@echo "$(GREEN)✓ Pre-commit hooks installed$(NC)"

pre-commit-run: ## Run pre-commit on all files
	@echo "$(BLUE)Running pre-commit checks...$(NC)"
	@pre-commit run --all-files
	@echo "$(GREEN)✓ Pre-commit checks complete$(NC)"

# Development setup
.PHONY: dev-setup

dev-setup: init pre-commit-install ## Complete development environment setup
	@echo "$(BLUE)Setting up development environment...$(NC)"
	@bash scripts/setup-dev.sh
	@echo "$(GREEN)✓ Development environment ready$(NC)"
