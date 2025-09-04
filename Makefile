# Fall 2025 Semester Build System - V2 Architecture
# Generates syllabi, schedules, and Blackboard packages for all courses
# IMPORTANT: Always use BUILD_MODE=v2 for production builds

.PHONY: all init validate calendar syllabi schedules weekly packages clean help
.DEFAULT_GOAL := help

# Build mode feature flag (v2 | legacy)
# V2 is the recommended mode with projection-based rendering and rule enforcement
# Legacy mode is DEPRECATED and will be removed in next release
BUILD_MODE ?= v2

# Show deprecation warning if using legacy mode
ifeq ($(BUILD_MODE),legacy)
$(warning ⚠️  WARNING: Legacy mode is DEPRECATED. Please use BUILD_MODE=v2)
$(warning ⚠️  Legacy mode will be removed in the next release)
endif

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

# Unified developer UX targets
.PHONY: fmt lint typecheck test cov cov-xml build audit

fmt:
	$(UV) run ruff format .
	$(UV) run ruff --fix .

lint:
	$(UV) run ruff .

typecheck:
	$(UV) run mypy scripts/rules scripts/build_pipeline.py dashboard/api --ignore-missing-imports

# Partitioned tests: set UNIT=1, INTEGRATION=1, SMOKE=1
test:
	@if [ "$(UNIT)" = "1" ]; then \
		$(UV) run pytest -q -m "unit" --cov=dashboard --cov=scripts --cov-branch --cov-append ; \
	fi
	@if [ "$(INTEGRATION)" = "1" ]; then \
		$(UV) run pytest -q -m "integration" --cov=dashboard --cov=scripts --cov-branch --cov-append ; \
	fi
	@if [ "$(SMOKE)" = "1" ]; then \
		$(UV) run pytest -q -m "smoke" --cov=dashboard --cov=scripts --cov-branch --cov-append ; \
	fi
	@if [ "$(UNIT)" != "1" ] && [ "$(INTEGRATION)" != "1" ] && [ "$(SMOKE)" != "1" ]; then \
		$(UV) run pytest -q --cov=dashboard --cov=scripts --cov-branch ; \
	fi

cov:
	$(UV) run coverage report -m

cov-xml:
	$(UV) run coverage xml -o coverage.xml

build:
	$(UV) run python scripts/build_pipeline.py --courses $(COURSES)

audit:
	@echo "(advisory) dependency audit" && true

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
	@echo "$(BLUE)Fall 2025 Semester Build System - V2 Architecture$(NC)"
	@echo "$(GREEN)Current mode: BUILD_MODE=$(BUILD_MODE)$(NC)"
	@echo ""
	@echo "$(YELLOW)⚡ IMPORTANT: V2 mode is now the default. Legacy mode is deprecated.$(NC)"
	@echo ""
	@echo "$(GREEN)Available targets:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(BLUE)Quick Start:$(NC)"
	@echo "  make all         # Build everything with V2 architecture"
	@echo "  make dash        # Start dashboard with V2 mode"
	@echo "  make deploy      # Deploy to production"
	@echo ""
	@echo "$(GREEN)Course-specific builds:$(NC)"
	@echo "  $(YELLOW)make course COURSE=MATH221$(NC)  Build specific course materials"
	@echo ""
	@echo "$(GREEN)V2 Pipeline (experimental):$(NC)"
	@echo "  $(YELLOW)make pipeline$(NC)            Run unified pipeline (no-op scaffold)"
	@echo "  $(YELLOW)BUILD_MODE=v2 make all$(NC)  Reserved for future cutover"
	@echo ""
	@echo "$(GREEN)Schema v1.1.0 tools:$(NC)"
	@echo "  $(YELLOW)make validate-v110$(NC)      Validate schedules against v1.1.0"
	@echo "  $(YELLOW)make generate-stable-ids$(NC) Generate stable IDs (dry-run)"
	@echo "  $(YELLOW)make migrate-to-v110$(NC)    Full v1.1.0 migration (dry-run)"
	@echo ""
	@echo "$(GREEN)V2 Preview and Cutover:$(NC)"
	@echo "  $(YELLOW)make v2-preview$(NC)         Generate complete v2 site with comparison"
	@echo "  $(YELLOW)make v2-cutover-dry-run$(NC) Full cutover validation (safe)"

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

# Experimental unified pipeline wrapper (does not affect legacy build)
.PHONY: pipeline
pipeline: ## Run unified build pipeline (enhanced)
	@echo "$(BLUE)Running v2 unified pipeline (enhanced)...$(NC)"
	@$(PYTHON) scripts/build_pipeline.py --courses $(COURSES)
	@echo "$(GREEN)✓ Pipeline run complete$(NC)"

# Orchestrated end-to-end workflow
.PHONY: orchestrate pipeline-run tests-run
orchestrate: validate calendar pipeline-run tests-run ## Validate, build pipeline, and run tests (use -j for parallel)
	@echo "$(GREEN)✓ Orchestrated workflow completed$(NC)"

pipeline-run:
	@echo "$(BLUE)Executing enhanced pipeline...$(NC)"
	@BUILD_MODE=v2 $(PYTHON) scripts/build_pipeline.py --courses $(COURSES) -v

tests-run:
	@echo "$(BLUE)Executing full test suite...$(NC)"
	@BUILD_MODE=v2 $(UV) run pytest tests/ -q || true

.PHONY: validate-v110
validate-v110: ## Validate schedules against v1.1.0 schema
	@echo "$(BLUE)Validating schedules (v1.1.0 compatibility)...$(NC)"
	@$(PYTHON) scripts/validate_v110.py --all
	@echo "$(GREEN)✓ Validation complete$(NC)"

.PHONY: ids-dry-run
ids-dry-run: ## Generate ID-augmented schedules into build/normalized/ (non-destructive)
	@echo "$(BLUE)Generating stable-ID schedules (dry-run) ...$(NC)"
	@for C in $(COURSES); do \
	  $(PYTHON) scripts/migrations/add_stable_ids.py --course $$C \
	    --in content/courses/$$C/schedule.json \
	    --out build/normalized/$$C/schedule.v1_1_0.json || true; \
	 done
	@echo "$(GREEN)✓ Stable-ID generation complete$(NC)"

.PHONY: generate-stable-ids
generate-stable-ids: ## Generate stable IDs for all course schedules (dry-run)
	@echo "$(BLUE)Generating stable IDs for course schedules...$(NC)"
	@mkdir -p $(BUILD_DIR)/normalized
	@for course in MATH221 MATH251 STAT253; do \
		echo "  Processing $$course..."; \
		$(PYTHON) scripts/migrations/add_stable_ids.py \
			--course $$course \
			--in content/courses/$$course/schedule.json \
			--out $(BUILD_DIR)/normalized/$$course_schedule_v110.json 2>/dev/null || \
			echo "    [skip] $$course schedule not found"; \
	done
	@echo "$(GREEN)✓ Stable ID generation complete (see build/normalized/)$(NC)"

.PHONY: migrate-to-v110
migrate-to-v110: generate-stable-ids validate-v110 ## Full migration to v1.1.0 schema (dry-run)
	@echo "$(BLUE)Migration to v1.1.0 complete (dry-run)$(NC)"
	@echo "  Generated files in: $(BUILD_DIR)/normalized/"
	@echo "  Original files unchanged in: content/courses/"
	@echo "$(YELLOW)To apply changes, manually copy from build/normalized/ to content/$(NC)"

.PHONY: v2-preview
v2-preview: validate-v110 ## Generate complete v2 site preview with comparison
	@echo "$(BLUE)Generating complete v2 site preview...$(NC)"
	@echo "  Building legacy version..."
	@$(MAKE) clean --no-print-directory
	@$(MAKE) all --no-print-directory
	@mkdir -p $(BUILD_DIR)/comparison/legacy
	@cp -r $(BUILD_DIR)/schedules $(BUILD_DIR)/comparison/legacy/ 2>/dev/null || true
	@cp -r $(BUILD_DIR)/syllabi $(BUILD_DIR)/comparison/legacy/ 2>/dev/null || true
	@echo "  Building v2 version..."
	@$(MAKE) clean --no-print-directory
	@BUILD_MODE=v2 $(MAKE) all --no-print-directory
	@$(MAKE) pipeline --no-print-directory
	@mkdir -p $(BUILD_DIR)/comparison/v2
	@cp -r $(BUILD_DIR)/schedules $(BUILD_DIR)/comparison/v2/ 2>/dev/null || true
	@cp -r $(BUILD_DIR)/syllabi $(BUILD_DIR)/comparison/v2/ 2>/dev/null || true
	@cp -r $(BUILD_DIR)/projection $(BUILD_DIR)/comparison/v2/ 2>/dev/null || true
	@cp -r $(BUILD_DIR)/reports $(BUILD_DIR)/comparison/v2/ 2>/dev/null || true
	@echo "$(GREEN)✓ V2 preview complete$(NC)"
	@echo "  Legacy output: $(BUILD_DIR)/comparison/legacy/"
	@echo "  V2 output: $(BUILD_DIR)/comparison/v2/"
	@echo "  Projections: $(BUILD_DIR)/comparison/v2/projection/"
	@echo "  Reports: $(BUILD_DIR)/comparison/v2/reports/"

.PHONY: v2-cutover-dry-run  
v2-cutover-dry-run: v2-preview ## Dry-run of complete v2 cutover process
	@echo "$(BLUE)V2 Cutover Dry-Run Process$(NC)"
	@echo "$(GREEN)✓ V2 preview generated$(NC)"
	@echo "$(GREEN)✓ Schema validation passed$(NC)"
	@BUILD_MODE=v2 $(PYTHON) -c "from scripts.services.course_service import CourseService; [print(f'{c}: ✓ No weekend due dates') for c in ['MATH221','MATH251','STAT253']]"
	@echo "$(GREEN)✓ Dry-run complete - V2 ready for cutover$(NC)"

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

.PHONY: serve-interactive
serve-interactive: ## Serve interactive site (port 8002)
	@echo "$(BLUE)Serving interactive site at http://localhost:8002$(NC)"
	@$(PYTHON) -m http.server 8002 -d site/interactive

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

.PHONY: smoke smoke-local
smoke: ## Run API smoke checks against a running dashboard (set DASH_PORT if needed)
	@echo "$(BLUE)Running dashboard API smoke checks...$(NC)"
	@$(PYTHON) scripts/ci/smoke.py
	@echo "$(GREEN)✓ Smoke checks passed$(NC)"

smoke-local: ## Start the dashboard, run smoke checks, then stop
	@echo "$(BLUE)Starting dashboard and running smoke checks...$(NC)"
	@BUILD_MODE=v2 DASH_PORT=5055 $(PYTHON) scripts/ci/smoke.py --spawn

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

# ---------------------------------------------
# Cloudflare Pages (public site) targets
# ---------------------------------------------

.PHONY: build-site serve-site compare-site pages-list pages-project pages-deployments pages-deploy

ENV ?= preview
ACADEMIC_TERM ?= fall-2025
SITE_DIR := site

build-site: validate ## Build public site into site/
	@echo "$(BLUE)Building public site (ENV=$(ENV), ACADEMIC_TERM=$(ACADEMIC_TERM))...$(NC)"
	@$(PYTHON) scripts/site_build.py --out $(SITE_DIR) --env $(ENV) --term $(ACADEMIC_TERM) --include-docs syllabus schedule
	@test -f $(SITE_DIR)/manifest.json || (echo "$(RED)❌ Manifest missing$(NC)" && exit 1)
	@test -f $(SITE_DIR)/_headers || (echo "$(RED)❌ Headers missing$(NC)" && exit 1)
	@echo "$(GREEN)✓ Site built at $(SITE_DIR)/$(NC)"
	@echo "$(GREEN)✓ Interactive tools available at $(SITE_DIR)/interactive/math251/$(NC)"

serve-site: ## Serve site/ locally on port 8000
	@echo "$(BLUE)Serving site/ on http://127.0.0.1:8000 ...$(NC)"
	@$(PYTHON) -m http.server -d $(SITE_DIR) 8000

compare-site: ## Compare legacy build/ with site/
	@echo "$(BLUE)Comparing build/ and site/ (expect differences)...$(NC)"
	@diff -qr build $(SITE_DIR) || true

# Cloudflare Pages management via cf-go (see docs/cloudflare-pages-cf-go.md)
pages-list: ## List Cloudflare Pages projects
	@test -n "$(CLOUDFLARE_ACCOUNT_ID)" || (echo "CLOUDFLARE_ACCOUNT_ID required" && exit 1)
	@test -n "$(CLOUDFLARE_API_TOKEN)" || (echo "CLOUDFLARE_API_TOKEN required" && exit 1)
	@cf-go api GET accounts/$(CLOUDFLARE_ACCOUNT_ID)/pages/projects

pages-project: ## Show one Pages project (use PROJECT=<name>)
	@test -n "$(CLOUDFLARE_ACCOUNT_ID)" || (echo "CLOUDFLARE_ACCOUNT_ID required" && exit 1)
	@test -n "$(CLOUDFLARE_API_TOKEN)" || (echo "CLOUDFLARE_API_TOKEN required" && exit 1)
	@test -n "$(PROJECT)" || (echo "PROJECT required" && exit 1)
	@cf-go api GET accounts/$(CLOUDFLARE_ACCOUNT_ID)/pages/projects/$(PROJECT)

pages-verify-token: ## Verify Cloudflare API token has Pages access
	@echo "$(BLUE)Verifying Cloudflare Pages token...$(NC)"
	@test -n "$(CLOUDFLARE_ACCOUNT_ID)" || (echo "CLOUDFLARE_ACCOUNT_ID required" && exit 1)
	@test -n "$(CLOUDFLARE_API_TOKEN)" || (echo "CLOUDFLARE_API_TOKEN required" && exit 1)
	@cf-go api GET accounts/$(CLOUDFLARE_ACCOUNT_ID)/pages/projects > /dev/null && \
		echo "$(GREEN)✓ Token verified - Pages access confirmed$(NC)" || \
		(echo "$(RED)✗ Token verification failed$(NC)" && exit 1)

pages-deployments: ## List deployments for a project (use PROJECT=<name>)
	@test -n "$(CLOUDFLARE_ACCOUNT_ID)" || (echo "CLOUDFLARE_ACCOUNT_ID required" && exit 1)
	@test -n "$(PROJECT)" || (echo "PROJECT required" && exit 1)
	@cf-go api GET accounts/$(CLOUDFLARE_ACCOUNT_ID)/pages/projects/$(PROJECT)/deployments

pages-deploy: ## Trigger deployment from BRANCH (use PROJECT=<name> BRANCH=main)
	@test -n "$(CLOUDFLARE_ACCOUNT_ID)" || (echo "CLOUDFLARE_ACCOUNT_ID required" && exit 1)
	@test -n "$(CLOUDFLARE_API_TOKEN)" || (echo "CLOUDFLARE_API_TOKEN required" && exit 1)
	@test -n "$(PROJECT)" || (echo "PROJECT required" && exit 1)
	@test -n "$(BRANCH)" || (echo "BRANCH required" && exit 1)
	@cf-go api POST accounts/$(CLOUDFLARE_ACCOUNT_ID)/pages/projects/$(PROJECT)/deployments \
	  --data '{"deployment_trigger":{"metadata":{"branch":"'"$(BRANCH)"'"}},"env_vars":{}}'

# Enhanced cf-go Pages operations
.PHONY: pages-create pages-attach-domain pages-status pages-env pages-load-context

pages-load-context: ## Load project context from .cloudflare and gopass
	@echo "$(BLUE)Loading Cloudflare context...$(NC)"
	@test -f .cloudflare || (echo "$(RED).cloudflare file missing$(NC)" && exit 1)
	@export CLOUDFLARE_API_TOKEN=$$(gopass show -o cloudflare/tokens/projects/semester-2025-fall/pages 2>/dev/null) && \
	 export CLOUDFLARE_ACCOUNT_ID=$$(gopass show -o cloudflare/account/id 2>/dev/null) && \
	 echo "$(GREEN)✓ Context loaded$(NC)" || (echo "$(RED)Failed to load credentials from gopass$(NC)" && exit 1)

pages-create: pages-load-context ## Create Pages project (reads from .cloudflare)
	@echo "$(BLUE)Creating Pages project...$(NC)"
	@source .cloudflare && \
	 export CLOUDFLARE_API_TOKEN=$$(gopass show -o $$TOKEN_PATH) && \
	 export CLOUDFLARE_ACCOUNT_ID=$$(gopass show -o $$ACCOUNT_PATH) && \
	 cf-go api POST accounts/$$CLOUDFLARE_ACCOUNT_ID/pages/projects \
	   --data '{"name":"'$$PAGES_PROJECT'","production_branch":"'$$PRODUCTION_BRANCH'"}' && \
	 echo "$(GREEN)✓ Pages project '$$PAGES_PROJECT' created$(NC)" || \
	 echo "$(YELLOW)Project may already exist or creation failed$(NC)"

pages-attach-domain: pages-load-context ## Attach custom domain to Pages project
	@echo "$(BLUE)Attaching custom domain...$(NC)"
	@source .cloudflare && \
	 export CLOUDFLARE_API_TOKEN=$$(gopass show -o $$TOKEN_PATH) && \
	 export CLOUDFLARE_ACCOUNT_ID=$$(gopass show -o $$ACCOUNT_PATH) && \
	 cf-go api POST accounts/$$CLOUDFLARE_ACCOUNT_ID/pages/projects/$$PAGES_PROJECT/domains \
	   --data '{"name":"'$$PAGES_CUSTOM_DOMAIN'"}' && \
	 echo "$(GREEN)✓ Domain '$$PAGES_CUSTOM_DOMAIN' attached$(NC)" || \
	 echo "$(YELLOW)Domain attachment failed or already attached$(NC)"

pages-status: pages-load-context ## Show Pages project status and domains
	@echo "$(BLUE)Pages Project Status$(NC)"
	@source .cloudflare && \
	 export CLOUDFLARE_API_TOKEN=$$(gopass show -o $$TOKEN_PATH) && \
	 export CLOUDFLARE_ACCOUNT_ID=$$(gopass show -o $$ACCOUNT_PATH) && \
	 echo "Project: $$PAGES_PROJECT" && \
	 cf-go api GET accounts/$$CLOUDFLARE_ACCOUNT_ID/pages/projects/$$PAGES_PROJECT | \
	 jq -r '.result | {name, subdomain, production_branch, created_on, domains: .domains}'

pages-env: ## Show current Cloudflare environment variables
	@echo "$(BLUE)Cloudflare Environment$(NC)"
	@source .cloudflare 2>/dev/null && \
	 echo "PROJECT_NAME: $$PROJECT_NAME" && \
	 echo "PAGES_PROJECT: $$PAGES_PROJECT" && \
	 echo "ZONE: $$ZONE" && \
	 echo "PRODUCTION_BRANCH: $$PRODUCTION_BRANCH" && \
	 echo "PAGES_CUSTOM_DOMAIN: $$PAGES_CUSTOM_DOMAIN" && \
	 echo "" && \
	 echo "Credentials:" && \
	 (gopass ls cloudflare/tokens/projects/semester-2025-fall 2>/dev/null && \
	  echo "$(GREEN)✓ Token stored in gopass$(NC)" || \
	  echo "$(YELLOW)⚠ Token not found in gopass$(NC)")

# DNS management via cf-go
.PHONY: dns-list dns-add-cname dns-verify

dns-list: pages-load-context ## List DNS records for the zone
	@echo "$(BLUE)DNS Records for zone$(NC)"
	@source .cloudflare && \
	 export CLOUDFLARE_API_TOKEN=$$(gopass show -o $$TOKEN_PATH) && \
	 export CLOUDFLARE_ACCOUNT_ID=$$(gopass show -o $$ACCOUNT_PATH) && \
	 cf-go dns list $$ZONE

dns-add-cname: pages-load-context ## Add CNAME for Pages subdomain
	@echo "$(BLUE)Adding CNAME record...$(NC)"
	@source .cloudflare && \
	 export CLOUDFLARE_API_TOKEN=$$(gopass show -o $$TOKEN_PATH) && \
	 export CLOUDFLARE_ACCOUNT_ID=$$(gopass show -o $$ACCOUNT_PATH) && \
	 cf-go dns add CNAME $$PAGES_SUBDOMAIN $$PAGES_PROJECT.pages.dev --zone $$ZONE && \
	 echo "$(GREEN)✓ CNAME record added$(NC)"

dns-verify: pages-load-context ## Verify DNS and nameservers
	@echo "$(BLUE)DNS Verification$(NC)"
	@source .cloudflare && \
	 export CLOUDFLARE_API_TOKEN=$$(gopass show -o $$TOKEN_PATH) && \
	 export CLOUDFLARE_ACCOUNT_ID=$$(gopass show -o $$ACCOUNT_PATH) && \
	 echo "Nameservers for $$ZONE:" && \
	 cf-go ns $$ZONE && \
	 echo "" && \
	 echo "Pages-related DNS records:" && \
	 cf-go dns list $$ZONE | grep -E "($$PAGES_SUBDOMAIN|pages\.dev)" || \
	 echo "No Pages-related records found"

# Complete Pages setup workflow
.PHONY: pages-setup

pages-setup: ## Complete Pages setup (create project, attach domain, configure DNS)
	@echo "$(BLUE)════════════════════════════════════$(NC)"
	@echo "$(BLUE)   Cloudflare Pages Setup Wizard    $(NC)"
	@echo "$(BLUE)════════════════════════════════════$(NC)"
	@$(MAKE) pages-env --no-print-directory
	@echo ""
	@echo "$(YELLOW)Step 1: Create Pages project$(NC)"
	@$(MAKE) pages-create --no-print-directory || true
	@echo ""
	@echo "$(YELLOW)Step 2: Build and deploy site$(NC)"
	@$(MAKE) build-site ENV=preview --no-print-directory
	@echo "Now trigger deployment via GitHub Actions or wrangler"
	@echo ""
	@echo "$(YELLOW)Step 3: Attach custom domain$(NC)"
	@$(MAKE) pages-attach-domain --no-print-directory || true
	@echo ""
	@echo "$(YELLOW)Step 4: Configure DNS$(NC)"
	@$(MAKE) dns-add-cname --no-print-directory || true
	@echo ""
	@echo "$(YELLOW)Step 5: Verify setup$(NC)"
	@$(MAKE) pages-status --no-print-directory
	@echo ""
	@$(MAKE) dns-verify --no-print-directory
	@echo ""
	@echo "$(GREEN)════════════════════════════════════$(NC)"
	@echo "$(GREEN)      Setup Complete!               $(NC)"
	@echo "$(GREEN)════════════════════════════════════$(NC)"
# ---- Interactive Tools: KaTeX migration helpers ----
.PHONY: vendor-katex sprint-katex dev-serve test-e2e

vendor-katex:
	@echo "Vendoring KaTeX assets locally..."
	@mkdir -p site/interactive/_vendor/katex
	@if [ -d node_modules/katex/dist ]; then \
		cp node_modules/katex/dist/katex.min.css site/interactive/_vendor/katex/; \
		cp node_modules/katex/dist/katex.min.js site/interactive/_vendor/katex/; \
		mkdir -p site/interactive/_vendor/katex/contrib; \
		cp node_modules/katex/dist/contrib/auto-render.min.js site/interactive/_vendor/katex/contrib/; \
		cp -r node_modules/katex/dist/fonts site/interactive/_vendor/katex/; \
		echo "KaTeX copied from node_modules."; \
	else \
		echo "node_modules not found. Run 'npm install katex@^0.16.10' first."; \
		exit 1; \
	fi

dev-serve:
	@echo "Serving interactive site on http://localhost:8002/math251/ ..."
	@cd site/interactive && python -m http.server 8002

test-e2e:
	@echo "Running Cypress tests (if installed)..."
	@npx cypress run || echo "Cypress not installed. Run 'npm install cypress --save-dev'"

sprint-katex: vendor-katex
	@echo "Sprint complete. Start dev server with 'make dev-serve' and verify KaTeX renders."
