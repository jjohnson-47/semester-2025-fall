## GIT
2cc10ee Remove outdated orchestration agent tests with API mismatches

## BRANCH
main

## TAGS (last 5)
v2025.09.03-v2-integration

## PY/TOOLS
Python 3.13.7
uv 0.8.14
pip 25.1.1 from /home/verlyn13/.local/lib/python3.13/site-packages/pip (python 3.13)

## OS
Linux fedora-top 6.16.3-200.fc42.x86_64 #1 SMP PREEMPT_DYNAMIC Sat Aug 23 17:02:17 UTC 2025 x86_64 GNU/Linux

## PYPROJECT (tool sections)
[tool.uv]
[tool.ruff]
[tool.ruff.lint]
[tool.ruff.format]
[tool.ruff.lint.isort]
[tool.black]
[tool.mypy]
[tool.pytest.ini_options]
[tool.coverage.run]
[tool.coverage.report]
[tool.coverage.html]

## MYPY/MAKE/PRE-COMMIT
[mypy]
ignore_missing_imports = True
warn_unused_ignores = True
show_error_codes = True
follow_imports = skip

[mypy-scripts.rules.*]
disallow_untyped_defs = True
warn_return_any = True
no_implicit_optional = True

[mypy-dashboard.api.*]
disallow_untyped_defs = True
disallow_untyped_decorators = False
warn_return_any = False

[mypy-scripts.rules.engine]
ignore_errors = True

[mypy-dashboard.api.deploy]
ignore_errors = True

[mypy-scripts.rules.dates_full]
ignore_errors = True

[mypy-scripts.migrations.*]
ignore_errors = True

[mypy-scripts.services.*]
ignore_errors = True

[mypy-scripts.utils.semester_calendar]
ignore_errors = True

[mypy-scripts.build_schedules]
ignore_errors = True

[mypy-scripts.build_syllabi]
ignore_errors = True

[mypy-dashboard.__init__]
ignore_errors = True
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
# Test targets for specific markers
test-unit: ## Run unit tests only
	$(UV) run pytest -m unit -v
test-integration: ## Run integration tests only  
	$(UV) run pytest -m integration -v
test-property: ## Run property-based tests only
	$(UV) run pytest -m property -v
test-solver: ## Run CP-SAT solver tests only
	$(UV) run pytest -m solver -v
test-fast: ## Run all tests except slow ones
	$(UV) run pytest -m "not slow" -v
test-all: ## Run all tests with coverage
	$(UV) run pytest --cov=dashboard --cov=scripts --cov-branch -v
cov:
	$(UV) run coverage report -m
cov-xml:
	$(UV) run coverage xml -o coverage.xml
ratchet:
	$(UV) run python scripts/ci/coverage_ratchet.py coverage.xml
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
repos:
  - repo: https://github.com/tox-dev/pyproject-fmt
    rev: 2.5.0
    hooks:
      - id: pyproject-fmt
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.5.7
    hooks:
      - id: ruff
        args: ["--fix"]
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v4.0.0-alpha.8
    hooks:
      - id: prettier
        args: ["--prose-wrap", "always"]
        additional_dependencies: ["prettier@3.3.3"]
  - repo: local
    hooks:
      - id: forbid-suppress
        name: forbid suppress outside startup
        entry: bash scripts/ci/forbid_suppress.sh
        language: system
        files: \.py$
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.10.0
    hooks:
      - id: mypy
        name: mypy (focused)
        additional_dependencies: []
        args:
          - scripts/rules
          - scripts/build_pipeline.py
          - dashboard/api
          - --ignore-missing-imports
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: check-yaml
      - id: end-of-file-fixer
      - id: trailing-whitespace

## WORKFLOWS (names)
.github/workflows/ci.yml
.github/workflows/coverage-summary.yml
.github/workflows/pages.yml
.github/workflows/release.yml
.github/workflows/scheduled.yml
.github/workflows/smoke.yml
.github/workflows/test.yml

## DEPLOY HINTS
#!/usr/bin/env python3
"""Deployment API for dashboard Deploy button.

Handles the complete deployment pipeline from build to verification,
integrating with the v2 templating architecture.
"""

import asyncio
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from flask import Blueprint, jsonify, request

# Create blueprint for deployment routes
deploy_bp = Blueprint("deploy", __name__, url_prefix="/api/deploy")

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
WORKER_DIR = PROJECT_ROOT.parent / "jeffsthings-courses"
SITE_DIR = PROJECT_ROOT / "site"
LOG_DIR = PROJECT_ROOT / "logs"

# Ensure log directory exists
LOG_DIR.mkdir(exist_ok=True)


class DeploymentManager:
    """Manages the deployment pipeline for course content."""

    def __init__(self):
        self.current_deployment: dict[str, Any] | None = None
        self.deployment_log: list[dict[str, Any]] = []
        self.is_deploying: bool = False

    async def run_command(
        self, cmd: str, cwd: Path | None = None, env: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Run a shell command asynchronously and capture output."""
        self.log(f"Running: {cmd}")

        # Merge environment variables
        cmd_env = os.environ.copy()
        if env:
            cmd_env.update(env)

        try:
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(cwd) if cwd else None,
                env=cmd_env,
            )

            stdout, stderr = await process.communicate()

            result = {
                "command": cmd,
                "returncode": process.returncode,
                "stdout": stdout.decode("utf-8"),
                "stderr": stderr.decode("utf-8"),
                "success": process.returncode == 0,
            }

            if not result["success"]:
                self.log(f"Command failed: {stderr.decode('utf-8')}", level="error")
            else:
                self.log("Command succeeded", level="success")

            return result

        except Exception as e:
            self.log(f"Command exception: {e!s}", level="error")
            return {
                "command": cmd,
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
                "success": False,
            }

    def log(self, message: str, level: str = "info"):
        """Add a message to the deployment log."""
        entry = {"timestamp": datetime.now().isoformat(), "level": level, "message": message}
        self.deployment_log.append(entry)

        # Also write to file
        log_file = LOG_DIR / f"deployment_{datetime.now().strftime('%Y%m%d')}.log"
        with open(log_file, "a") as f:
            f.write(f"[{entry['timestamp']}] [{entry['level'].upper()}] {entry['message']}\n")

    async def build_site(self) -> dict[str, Any]:
        """Build the site with v2 templating."""
        self.log("Starting site build with v2 mode")

        result = await self.run_command(
            "make build-site", cwd=PROJECT_ROOT, env={"BUILD_MODE": "v2", "ENV": "production"}
        )

        # Verify site was built
        if result["success"]:
            manifest_path = SITE_DIR / "manifest.json"
            if manifest_path.exists():
                self.log("Site build completed successfully", level="success")
            else:
                result["success"] = False
                result["stderr"] = "Site build completed but manifest.json not found"
                self.log("Site build failed: manifest missing", level="error")

        return result

    async def sync_content(self) -> dict[str, Any]:
        """Sync content to jeffsthings-courses."""
        self.log("Syncing content to worker directory")

        if not WORKER_DIR.exists():
            self.log(f"Worker directory not found: {WORKER_DIR}", level="error")
            return {"success": False, "stderr": f"Worker directory not found: {WORKER_DIR}"}

        result = await self.run_command("pnpm sync", cwd=WORKER_DIR)

        if result["success"]:
            self.log("Content sync completed", level="success")

        return result

    async def deploy_worker(self) -> dict[str, Any]:
        """Deploy to Cloudflare Workers."""
        self.log("Deploying to Cloudflare Workers")

        result = await self.run_command("pnpm deploy", cwd=WORKER_DIR)

        if result["success"]:
            # Extract deployment URL from output
            output = result["stdout"]
            if "courses.jeffsthings.com" in output:
                self.log("Worker deployment successful", level="success")
            else:
                self.log("Worker deployed but URL not confirmed", level="warning")

        return result

    async def verify_deployment(self) -> dict[str, Any]:
        """Verify the deployment is working."""
        self.log("Verifying deployment")

        result = await self.run_command("pnpm verify", cwd=WORKER_DIR)

        if result["success"]:
            self.log("Deployment verification passed", level="success")
        else:
            self.log("Deployment verification failed", level="warning")

        return result

    async def execute_full_deployment(self) -> dict[str, Any]:
        """Execute the complete deployment pipeline."""
        if self.is_deploying:
            return {"status": "error", "message": "Deployment already in progress"}

        self.is_deploying = True
        self.deployment_log = []
        start_time = datetime.now()

        self.log("Starting full deployment pipeline")

        deployment_result = {
            "status": "success",
            "start_time": start_time.isoformat(),
            "steps": {},
            "production_url": "https://courses.jeffsthings.com",
        }

        try:
            # Step 1: Build site with v2 mode
            self.log("Step 1/4: Building site", level="info")
            build_result = await self.build_site()
            deployment_result["steps"]["build"] = {
                "success": build_result["success"],
                "duration": (datetime.now() - start_time).total_seconds(),
            }

            if not build_result["success"]:
                raise Exception(f"Build failed: {build_result.get('stderr', 'Unknown error')}")

            # Step 2: Sync content
            self.log("Step 2/4: Syncing content", level="info")
            sync_start = datetime.now()
            sync_result = await self.sync_content()
            deployment_result["steps"]["sync"] = {
                "success": sync_result["success"],
                "duration": (datetime.now() - sync_start).total_seconds(),
            }

            if not sync_result["success"]:
                raise Exception(f"Sync failed: {sync_result.get('stderr', 'Unknown error')}")

            # Step 3: Deploy to Cloudflare

## COURSES SUMMARY
{
  "courses_dir_exists": true,
  "course_count": 3,
  "courses": [
    {
      "course_code": "MATH221",
      "json_files": 14,
      "has_manifest": false,
      "schema_version": null
    },
    {
      "course_code": "MATH251",
      "json_files": 14,
      "has_manifest": false,
      "schema_version": null
    },
    {
      "course_code": "STAT253",
      "json_files": 14,
      "has_manifest": false,
      "schema_version": null
    }
  ]
}

## LARGE TEMPLATES (>2000 lines or >80KB)

## DB TABLES
deps
events
now_queue
scores
sqlite_sequence
tasks
tasks_fts
tasks_fts_config
tasks_fts_data
tasks_fts_docsize
tasks_fts_idx

## TASKS COLS
0|id|TEXT|0||1
1|course|TEXT|0||0
2|title|TEXT|1||0
3|status|TEXT|1||0
4|due_at|TEXT|0||0
5|est_minutes|INTEGER|0||0
6|weight|REAL|0|1.0|0
7|category|TEXT|0||0
8|anchor|INTEGER|0|0|0
9|notes|TEXT|0||0
10|created_at|TEXT|1||0
11|updated_at|TEXT|1||0
12|checklist|TEXT|0||0
13|parent_id|TEXT|0||0

## COURSE REGISTRY COLS

## COURSE PROJECTION COLS

## EVENTS COLS
0|id|INTEGER|0||1
1|at|TEXT|1||0
2|task_id|TEXT|1||0
3|field|TEXT|1||0
4|from_val|TEXT|0||0
5|to_val|TEXT|0||0

## ROW COUNTS
tasks: 55
now_queue: 0
tasks has origin_* cols (count of 3): 0

## TESTS (collect-only excerpt)

## MARKERS

## RUFF
ruff.toml: none

## TYPE CHECK
3:warn_unused_ignores = True
9:warn_return_any = True
15:warn_return_any = False

## QUICK TAKEAWAYS
- Courses detected: 3 (manifests present: 0)
- DB present: yes
- Projection cache: missing
- Course registry: missing
- Events table: present
- Templates indexed: 25 (see templates_report.csv; watch large files section)
- Pytest markers recorded (see _pytest_markers.txt).
