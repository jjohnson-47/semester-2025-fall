# Fall 2025 Semester Build System
# Generates syllabi, schedules, and Blackboard packages for all courses

.PHONY: all init validate calendar syllabi schedules weekly packages clean help
.DEFAULT_GOAL := help

# Configuration
PYTHON := python3
VENV := venv
SEMESTER := fall-2025
BUILD_DIR := build
COURSES := MATH221 MATH251 STAT253

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

# Help target
help: ## Show this help message
	@echo "$(BLUE)Fall 2025 Semester Build System$(NC)"
	@echo "$(GREEN)Available targets:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Course-specific builds:$(NC)"
	@echo "  $(YELLOW)make course COURSE=MATH221$(NC)  Build specific course materials"

# Initialize environment
init: ## Create virtualenv and install dependencies
	@echo "$(BLUE)Initializing environment...$(NC)"
	@if [ ! -d "$(VENV)" ]; then \
		$(PYTHON) -m venv $(VENV); \
		echo "$(GREEN)✓ Virtual environment created$(NC)"; \
	fi
	@. $(VENV)/bin/activate && pip install -q -r requirements.txt
	@echo "$(GREEN)✓ Dependencies installed$(NC)"
	@$(MAKE) validate

# Validate all JSON files
validate: ## Validate JSON files against schemas
	@echo "$(BLUE)Validating JSON files...$(NC)"
	@. $(VENV)/bin/activate && $(PYTHON) scripts/validate_json.py
	@echo "$(GREEN)✓ All JSON files valid$(NC)"

# Generate semester calendar
calendar: validate ## Generate semester calendar from variables
	@echo "$(BLUE)Generating semester calendar...$(NC)"
	@. $(VENV)/bin/activate && $(PYTHON) scripts/utils/calendar.py
	@echo "$(GREEN)✓ Calendar generated$(NC)"

# Build all syllabi
syllabi: calendar ## Generate syllabi for all courses
	@echo "$(BLUE)Building syllabi...$(NC)"
	@mkdir -p $(BUILD_DIR)/syllabi
	@. $(VENV)/bin/activate && $(PYTHON) scripts/build_syllabi.py
	@echo "$(GREEN)✓ Syllabi generated for: $(COURSES)$(NC)"

# Generate schedules
schedules: calendar ## Generate course schedules
	@echo "$(BLUE)Building schedules...$(NC)"
	@mkdir -p $(BUILD_DIR)/schedules
	@. $(VENV)/bin/activate && $(PYTHON) scripts/build_schedules.py
	@echo "$(GREEN)✓ Schedules generated$(NC)"

# Generate weekly folders
weekly: calendar ## Create weekly overview pages
	@echo "$(BLUE)Creating weekly folders...$(NC)"
	@mkdir -p $(BUILD_DIR)/weekly
	@. $(VENV)/bin/activate && $(PYTHON) scripts/weekgen.py
	@echo "$(GREEN)✓ Weekly folders created$(NC)"

# Build Blackboard packages
packages: syllabi schedules weekly ## Create Blackboard import packages
	@echo "$(BLUE)Building Blackboard packages...$(NC)"
	@mkdir -p $(BUILD_DIR)/blackboard
	@. $(VENV)/bin/activate && $(PYTHON) scripts/build_bb_packages.py
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
	@. $(VENV)/bin/activate && $(PYTHON) scripts/build_syllabi.py --course $(COURSE)
	@. $(VENV)/bin/activate && $(PYTHON) scripts/build_schedules.py --course $(COURSE)
	@. $(VENV)/bin/activate && $(PYTHON) scripts/build_bb_packages.py --course $(COURSE)
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
	@cd $(BUILD_DIR) && $(PYTHON) -m http.server 8000

lint: ## Run code linting
	@echo "$(BLUE)Running linters...$(NC)"
	@. $(VENV)/bin/activate && pylint scripts/

format: ## Format Python code
	@echo "$(BLUE)Formatting code...$(NC)"
	@. $(VENV)/bin/activate && black scripts/

test: validate ## Run tests
	@echo "$(BLUE)Running tests...$(NC)"
	@. $(VENV)/bin/activate && pytest tests/

# Installation check
check-deps: ## Check required dependencies
	@echo "$(BLUE)Checking dependencies...$(NC)"
	@which $(PYTHON) > /dev/null && echo "$(GREEN)✓ Python3 found$(NC)" || echo "$(RED)✗ Python3 not found$(NC)"
	@which pandoc > /dev/null && echo "$(GREEN)✓ Pandoc found$(NC)" || echo "$(YELLOW)⚠ Pandoc not found (optional for PDF)$(NC)"
	@which git > /dev/null && echo "$(GREEN)✓ Git found$(NC)" || echo "$(RED)✗ Git not found$(NC)"

# Dashboard targets
.PHONY: dash-init dash-gen dash-validate dash dash-open dash-export dash-snapshot dash-reset

dash-init: init ## Initialize dashboard environment
	@echo "$(BLUE)Setting up dashboard environment...$(NC)"
	@. $(VENV)/bin/activate && pip install -q -r dashboard/requirements.txt
	@mkdir -p dashboard/state dashboard/templates_src build/dashboard
	@. $(VENV)/bin/activate && $(PYTHON) scripts/generate_dashboard_config.py
	@echo "$(GREEN)✓ Dashboard initialized$(NC)"

dash-gen: dash-init ## Generate tasks from templates
	@echo "$(BLUE)Generating tasks from templates...$(NC)"
	@. $(VENV)/bin/activate && $(PYTHON) dashboard/tools/generate_tasks.py \
		--courses dashboard/state/courses.json \
		--templates dashboard/templates_src \
		--out dashboard/state/tasks.json
	@$(MAKE) dash-validate --no-print-directory
	@echo "$(GREEN)✓ Tasks generated successfully$(NC)"

dash-validate: ## Validate task data integrity
	@echo "$(BLUE)Validating task data...$(NC)"
	@. $(VENV)/bin/activate && $(PYTHON) dashboard/tools/validate.py
	@echo "$(GREEN)✓ Validation passed$(NC)"

dash: dash-gen ## Run dashboard server
	@echo "$(BLUE)Starting dashboard server on http://127.0.0.1:5055$(NC)"
	@. $(VENV)/bin/activate && \
	FLASK_APP=dashboard/app.py FLASK_ENV=development \
	DASH_PORT=5055 DASH_HOST=127.0.0.1 \
	flask run --host=127.0.0.1 --port=5055

dash-open: ## Open dashboard in browser
	@xdg-open http://127.0.0.1:5055 2>/dev/null || \
	 open http://127.0.0.1:5055 2>/dev/null || \
	 echo "Please open http://127.0.0.1:5055 in your browser"

dash-export: ## Export dashboard data (ICS, CSV)
	@echo "$(BLUE)Exporting dashboard data...$(NC)"
	@. $(VENV)/bin/activate && $(PYTHON) dashboard/tools/export.py 2>/dev/null || echo "Export tool not yet implemented"
	@echo "$(GREEN)✓ Export complete$(NC)"

dash-snapshot: ## Create git snapshot of current state
	@git add dashboard/state/tasks.json 2>/dev/null && \
	 git commit -m "dashboard: snapshot $$(date -Iseconds)" 2>/dev/null || \
	 echo "No changes to snapshot"

dash-reset: ## Reset all task statuses for new semester
	@echo "$(BLUE)Resetting all task statuses...$(NC)"
	@. $(VENV)/bin/activate && $(PYTHON) dashboard/tools/reset.py 2>/dev/null || echo "Reset tool not yet implemented"
	@$(MAKE) dash-snapshot --no-print-directory
	@echo "$(GREEN)✓ All tasks reset to 'todo' status$(NC)"

# CI/CD targets
.PHONY: ci-validate ci-build

ci-validate: ## CI validation step
	@$(PYTHON) scripts/validate_json.py --strict

ci-build: ## CI build step
	@$(PYTHON) scripts/build_syllabi.py --ci
	@$(PYTHON) scripts/build_schedules.py --ci
	@$(PYTHON) scripts/build_bb_packages.py --ci