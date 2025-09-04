#!/usr/bin/env python3
"""One-time migration from JSON to SQLite.

Reads dashboard/state/tasks.json and imports into dashboard/state/tasks.db.
Safe to re-run; performs upserts by task id. Reports counts.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from dashboard.db import Database, DatabaseConfig


def main() -> None:
    state_dir = Path("dashboard/state")
    tasks_json = state_dir / "tasks.json"
    db_path = state_dir / "tasks.db"

    if not tasks_json.exists():
        print(f"No tasks.json found at {tasks_json}")
        return

    db = Database(DatabaseConfig(db_path))
    db.initialize()

    summary = db.import_tasks_json(tasks_json)
    health = db.health()

    report: dict[str, Any] = {
        "db": str(db_path),
        "inserted": summary["inserted"],
        "updated": summary["updated"],
        "deps": summary["deps"],
        "health": health,
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

