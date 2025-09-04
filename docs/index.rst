Fall 2025 Dashboard Documentation
==================================

Welcome to the comprehensive documentation for the Fall 2025 Course Management Dashboard.

This system provides a modern, dependency-aware task management platform built with
Flask 3.x and HTMX 2.x, following the latest Python 3.13 best practices.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   introduction
   architecture
   api/index
   models/index
   services/index
   testing
   deployment

Quick Start
-----------

Installation
^^^^^^^^^^^^

.. code-block:: bash

   # Clone the repository
   git clone <repository-url>
   cd semester-2025-fall

   # Install dependencies with UV
   uv sync --all-extras

   # Initialize the database
   uv run flask init-db

   # Run the development server
   make dash

Key Features
------------

**Dependency Management**
   Tasks can depend on other tasks, automatically blocking and unblocking
   based on completion status.

**Hierarchical Organization**
   Tasks support parent-child relationships for visual organization
   while maintaining functional dependencies.

**HTMX-Powered UI**
   Real-time updates using HTMX out-of-band swaps, providing a reactive
   interface without heavy JavaScript frameworks.

**Multiple Views**
   - **List View**: Hierarchical task display with expandable sections
   - **Kanban Board**: Drag-and-drop task management across status columns
   - **Command Palette**: Keyboard-driven task operations (Cmd+K)

**Smart Filtering**
   Advanced filtering by course, status, category, assignee, and special
   filters like overdue tasks and critical path.

Architecture Overview
---------------------

The dashboard follows a layered architecture:

.. code-block:: text

   ┌─────────────────────────────────────┐
   │         HTMX Frontend               │
   │   (Templates + Alpine.js)           │
   └─────────────────────────────────────┘
                    │
   ┌─────────────────────────────────────┐
   │         Flask 3.x API               │
   │   (Blueprints + Routes)             │
   └─────────────────────────────────────┘
                    │
   ┌─────────────────────────────────────┐
   │       Service Layer                 │
   │         (DependencyService)         │
   └─────────────────────────────────────┘
                    │
   ┌─────────────────────────────────────┐
   │         Data Models                 │
   │    (Task, TaskGraph, Enums)         │
   └─────────────────────────────────────┘
                    │
   ┌─────────────────────────────────────┐
   │       Storage Layer                 │
   │      (SQLite DB with JSON I/O)      │
   └─────────────────────────────────────┘

API Documentation
-----------------

The dashboard provides a comprehensive RESTful API:

**Task Management**
   - ``GET /api/tasks`` - List tasks with filtering
   - ``POST /api/tasks`` - Create new task
   - ``PUT /api/tasks/<id>`` - Update task
   - ``DELETE /api/tasks/<id>`` - Delete task

**Status Updates**
   - ``POST /api/tasks/<id>/status`` - Update status with dependency resolution
   - ``POST /api/tasks/<id>/complete`` - Quick complete with auto-unlocking

**Views**
   - ``GET /api/tasks/list`` - HTML list view
   - ``GET /api/tasks/kanban`` - HTML Kanban board
   - ``GET /api/tasks/<id>/children`` - Lazy-load child tasks

**Export**
   - ``GET /api/export/csv`` - Export as CSV
   - ``GET /api/export/json`` - Export as JSON
   - ``GET /api/export/ics`` - Export as calendar

Testing
-------

The project includes comprehensive testing:

.. code-block:: bash

   # Run all tests with coverage
   uv run pytest --cov=dashboard --cov=scripts

   # Run specific test categories
   uv run pytest -m unit        # Unit tests only
   uv run pytest -m integration # Integration tests
   uv run pytest -m slow        # Performance tests

Test coverage target: **80%+**

Development Workflow
--------------------

1. **Create feature branch**::

    git checkout -b feature/your-feature

2. **Make changes and test**::

    make test
    make lint
    make format

3. **Build and verify**::

    make all

4. **Commit with conventional commits**::

    git commit -m "feat: add new feature"

5. **Create pull request**

Deployment
----------

The dashboard can be deployed using:

- **Development**: ``make dash`` (Flask development server)
- **Production**: Gunicorn + nginx (see deployment guide)
- **Docker**: ``docker-compose up`` (containerized deployment)

License
-------

Copyright 2025 - Course Management Team

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
