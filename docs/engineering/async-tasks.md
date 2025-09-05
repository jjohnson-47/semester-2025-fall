# Async Task Lifecycle Policy

This repo enforces safe patterns for background tasks and structured concurrency.

- Endpoints: never use `asyncio.create_task` directly; prefer framework-provided `BackgroundTasks`.
- App workers: store tasks in a module-level set; add a `done_callback`; cancel and `await gather` on shutdown.
- Fan-out: prefer `asyncio.TaskGroup` when you can await completion in-scope.
- Always name tasks (`name="..."`) and ensure exceptions are surfaced (done callback or awaited paths).

Examples

```py
_bg_tasks: set[asyncio.Task[None]] = set()

def _track_task(t: asyncio.Task[None]) -> None:
    _bg_tasks.add(t)
    t.add_done_callback(_bg_tasks.discard)

# Long-lived worker
t = asyncio.create_task(worker_loop(), name="worker_loop")
_track_task(t)

# Structured fan-out
async with asyncio.TaskGroup() as tg:
    tg.create_task(do_one(), name="do_one")
    tg.create_task(do_two(), name="do_two")
```

