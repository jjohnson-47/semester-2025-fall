API Reference
=============

This section provides detailed API documentation for all modules in the dashboard.

Models
------

.. automodule:: dashboard.models
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Task Model
^^^^^^^^^^

.. autoclass:: dashboard.models.Task
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

   .. automethod:: to_dict
   .. automethod:: from_dict
   .. automethod:: is_blocked
   .. automethod:: can_start
   .. automethod:: update_status_from_dependencies

TaskGraph Model
^^^^^^^^^^^^^^^

.. autoclass:: dashboard.models.TaskGraph
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

   .. automethod:: add_task
   .. automethod:: get_task
   .. automethod:: get_children
   .. automethod:: get_blockers
   .. automethod:: get_blocked_by
   .. automethod:: mark_completed
   .. automethod:: topological_sort
   .. automethod:: get_critical_path

Services
--------

DependencyService
^^^^^^^^^^^^^^^^^

.. automodule:: dashboard.services.dependency_service
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: dashboard.services.dependency_service.DependencyService
   :members:
   :undoc-members:
   :show-inheritance:

   Key Methods:

   .. automethod:: build_task_graph
   .. automethod:: get_task_hierarchy
   .. automethod:: complete_task
   .. automethod:: update_task_status
   .. automethod:: get_critical_path
   .. automethod:: validate_dependencies

TaskService
^^^^^^^^^^^

.. automodule:: dashboard.services.task_service
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: dashboard.services.task_service.TaskService
   :members:
   :undoc-members:
   :show-inheritance:

API Endpoints
-------------

Task Management Endpoints
^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: dashboard.api.tasks
   :members:
   :undoc-members:
   :show-inheritance:

HTMX Endpoints
^^^^^^^^^^^^^^

.. automodule:: dashboard.api.tasks_htmx
   :members:
   :undoc-members:
   :show-inheritance:

Export Endpoints
^^^^^^^^^^^^^^^^

.. automodule:: dashboard.api.export
   :members:
   :undoc-members:
   :show-inheritance:

Utilities
---------

Decorators
^^^^^^^^^^

.. automodule:: dashboard.utils.decorators
   :members:
   :undoc-members:
   :show-inheritance:

Task Generation
^^^^^^^^^^^^^^^

.. automodule:: dashboard.tools.generate_tasks_with_deps
   :members:
   :undoc-members:
   :show-inheritance:
