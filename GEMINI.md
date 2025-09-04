# Gemini Code Assistant Context

This document provides context for the Gemini Code Assistant to understand the "Fall 2025 Semester Course Management System" project.

## Project Overview

This project is a comprehensive course management system for the Fall 2025 semester at Kenai Peninsula College. It automates the generation of syllabi, schedules, and other course materials for three courses: MATH 221, MATH 251, and STAT 253.

The system is built on a "V2 Architecture" which utilizes a projection-based rendering system. Course data is stored in JSON files and then processed by a series of Python scripts to generate the final HTML and other output files.

The project also includes a sophisticated Flask-based dashboard for task management, deployment, and viewing generated content. The dashboard provides a rich API for interacting with the system.

### Key Technologies

*   **Backend:** Python 3.13+, Flask
*   **Frontend:** Jinja2, HTML, CSS, Bootstrap, HTMX
*   **Database:** SQLite
*   **Build & Automation:** `make`, `uv`
*   **Dependencies:**
    *   Python: `jinja2`, `pyyaml`, `jsonschema`, `flask`, `pytest`, `ruff`, `mypy`
    *   Node.js: `katex` (for mathematical notation)
*   **Deployment:** Cloudflare Pages, with `cf-go` for API interactions.

### Architecture

*   **Data:** Course data is stored in JSON files within the `content/courses` directory. Task data is stored in an SQLite database at `dashboard/state/tasks.db`.
*   **Build:** The `Makefile` orchestrates the entire build process. Python scripts in the `scripts` directory handle the logic for generating syllabi, schedules, and other materials.
*   **Dashboard:** The `dashboard` directory contains a Flask application that provides a web-based interface for managing the system. It includes a task management system with intelligent prioritization, a viewer for generated content, and deployment tools.
*   **Output:** The `build` directory contains the generated files, and the `site` directory contains the final static site for deployment.

## Task Management System

The task management system is a key feature of the dashboard. It has the following components:

*   **Database Backend:** Task data is stored in an SQLite database. The schema is defined in `dashboard/db/repo.py`.
*   **Prioritization Service:** A `PrioritizationService` (`dashboard/services/prioritization.py`) calculates "smart scores" for tasks based on their dependencies, phase, and other metrics.
*   **"Now Queue":** The system generates a "Now Queue" of high-priority tasks that should be addressed immediately.
*   **Task Orchestration:** A `TaskOrchestrator` (`dashboard/orchestrator.py`) can analyze the task dependency graph, detect cycles, and suggest optimizations.
*   **Agent Coordination:** An `AgentCoordinator` can manage multiple "agents" for automated task execution.

## Building and Running

The project is managed through a series of `make` commands. The `BUILD_MODE=v2` environment variable is required for all V2 architecture operations.

### Core Commands

*   **Initialize the environment:**
    ```bash
    make init
    ```
*   **Build all course materials:**
    ```bash
    BUILD_MODE=v2 make all
    ```
*   **Start the task dashboard:**
    ```bash
    BUILD_MODE=v2 make dash
    ```
    The dashboard will be available at `http://localhost:5055`.

### Development Commands

*   **Run tests:**
    ```bash
    make test
    ```
*   **Lint the code:**
    ```bash
    make lint
    ```
*   **Format the code:**
    ```bash
    make format
    ```

## Development Conventions

*   **Code Style:** The project uses `ruff` and `black` for Python code formatting and linting. Configuration is in `pyproject.toml`.
*   **Type Checking:** `mypy` is used for static type checking. Configuration is in `pyproject.toml`.
*   **Testing:** `pytest` is the testing framework. Tests are located in the `tests` directory.
*   **Dependencies:** Python dependencies are managed with `uv` and are listed in `pyproject.toml`. Node.js dependencies are in `package.json`.
*   **V2 Architecture:** All new development should adhere to the V2 architecture and use the `BUILD_MODE=v2` flag.
*   **Commits:** Pre-commit hooks are available and can be installed with `make pre-commit-install`.