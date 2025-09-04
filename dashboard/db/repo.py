"""SQLite repository layer for task system.

This module encapsulates all database access and schema creation.
It is designed to be deterministic, simple, and safe for local use.

Key design goals:
- Explicit schema creation (DDL here) with WAL and busy_timeout
- Functions with clear names and type hints
- No ORMs; use `sqlite3` directly with row_factory dicts
- Import/export helpers for JSON compatibility
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Generator, Iterable, Optional


# ------------------------------
# Connection utilities
# ------------------------------


def _utcnow_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


@dataclass
class DatabaseConfig:
    db_path: Path
    enable_wal: bool = True
    busy_timeout_ms: int = 2000


class Database:
    """Minimal repository API over SQLite.

    Usage:
        db = Database(DatabaseConfig(Path("dashboard/state/tasks.db")))
        db.initialize()
    """

    def __init__(self, config: DatabaseConfig) -> None:
        self.config = config
        self.db_path = config.db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def connect(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            if self.config.enable_wal:
                conn.execute("PRAGMA journal_mode=WAL")
            if self.config.busy_timeout_ms:
                conn.execute(f"PRAGMA busy_timeout={int(self.config.busy_timeout_ms)}")
            yield conn
            conn.commit()
        finally:
            conn.close()

    # ------------------------------
    # Schema management
    # ------------------------------

    def initialize(self) -> None:
        """Create tables if they do not exist."""
        ddl = [
            """
            create table if not exists tasks(
                id text primary key,
                course text,
                title text not null,
                status text check(status in ('todo','doing','review','done','blocked')) not null,
                due_at text,
                est_minutes integer,
                weight real default 1.0,
                category text,
                anchor integer default 0,
                notes text,
                created_at text not null,
                updated_at text not null
            )
            """,
            """
            create table if not exists deps(
                task_id text not null,
                blocks_id text not null,
                primary key(task_id, blocks_id)
            )
            """,
            """
            create table if not exists events(
                id integer primary key autoincrement,
                at text not null,
                task_id text not null,
                field text not null,
                from_val text,
                to_val text
            )
            """,
            """
            create table if not exists scores(
                task_id text primary key,
                score real not null,
                factors text not null, -- JSON string
                computed_at text not null
            )
            """,
            """
            create table if not exists now_queue(
                pos integer primary key,
                task_id text not null
            )
            """,
            # Optional FTS virtual table
            """
            create virtual table if not exists tasks_fts using fts5(
                title, notes, content='tasks', content_rowid='rowid'
            )
            """,
        ]

        with self.connect() as conn:
            for statement in ddl:
                conn.execute(statement)

            # lightweight indices
            conn.execute("create index if not exists idx_tasks_status on tasks(status)")
            conn.execute("create index if not exists idx_tasks_course on tasks(course)")
            conn.execute("create index if not exists idx_tasks_due on tasks(due_at)")
            conn.execute("create index if not exists idx_deps_task on deps(task_id)")
            conn.execute("create index if not exists idx_deps_blocks on deps(blocks_id)")
            # Add optional columns if absent
            try:
                conn.execute("alter table tasks add column checklist text")
            except sqlite3.DatabaseError:
                pass

    # ------------------------------
    # Import / Export
    # ------------------------------

    def import_tasks_json(self, tasks_json_path: Path) -> dict[str, int]:
        """Import tasks JSON into DB. Idempotent by task id.

        Returns a summary dict with counts.
        """
        with open(tasks_json_path) as f:
            payload = json.load(f)

        tasks: list[dict[str, Any]] = payload.get("tasks", [])
        inserted = 0
        updated = 0
        deps_inserted = 0

        with self.connect() as conn:
            for task in tasks:
                task_id = task.get("id")
                if not task_id:
                    continue
                now_iso = _utcnow_iso()
                fields = {
                    "id": task_id,
                    "course": task.get("course"),
                    "title": task.get("title") or "",
                    "status": task.get("status") or "todo",
                    "due_at": task.get("due_date") or task.get("due"),
                    "est_minutes": task.get("est_minutes"),
                    "weight": float(task.get("weight", 1.0)),
                    "category": task.get("category"),
                    "anchor": 1 if task.get("anchor") else 0,
                    "notes": task.get("description") or task.get("notes"),
                    "created_at": task.get("created_at") or now_iso,
                    "updated_at": task.get("updated_at") or now_iso,
                }

                cur = conn.execute("select 1 from tasks where id=?", (task_id,))
                exists = cur.fetchone() is not None
                if exists:
                    conn.execute(
                        """
                        update tasks set course=:course, title=:title, status=:status,
                               due_at=:due_at, est_minutes=:est_minutes, weight=:weight,
                               category=:category, anchor=:anchor, notes=:notes, updated_at=:updated_at
                         where id=:id
                        """,
                        fields,
                    )
                    updated += 1
                else:
                    conn.execute(
                        """
                        insert into tasks(id, course, title, status, due_at, est_minutes, weight, category, anchor, notes, created_at, updated_at)
                        values(:id, :course, :title, :status, :due_at, :est_minutes, :weight, :category, :anchor, :notes, :created_at, :updated_at)
                        """,
                        fields,
                    )
                    inserted += 1

                # deps
                for dep_id in (task.get("depends_on") or []):
                    try:
                        conn.execute(
                            "insert or ignore into deps(task_id, blocks_id) values(?, ?)",
                            (task_id, dep_id),
                        )
                        deps_inserted += 1
                    except sqlite3.DatabaseError:
                        # ignore malformed dep rows in import
                        pass

        return {"inserted": inserted, "updated": updated, "deps": deps_inserted}

    def export_tasks_json(self) -> dict[str, Any]:
        """Export all tasks to a JSON payload compatible with original files."""
        with self.connect() as conn:
            rows = conn.execute(
                "select id, course, title, status, due_at, est_minutes, weight, category, anchor, notes, checklist, created_at, updated_at from tasks"
            ).fetchall()
            deps = conn.execute("select task_id, blocks_id from deps").fetchall()

        tasks: list[dict[str, Any]] = []
        deps_map: dict[str, list[str]] = {}
        for row in deps:
            deps_map.setdefault(row["task_id"], []).append(row["blocks_id"])  # type: ignore[index]

        for row in rows:
            task = {
                "id": row["id"],
                "course": row["course"],
                "title": row["title"],
                "status": row["status"],
                "due_date": row["due_at"],
                "est_minutes": row["est_minutes"],
                "weight": row["weight"],
                "category": row["category"],
                "anchor": bool(row["anchor"]),
                "description": row["notes"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
            # Include checklist if present
            if row["checklist"]:
                try:
                    import json as _json

                    task["checklist"] = _json.loads(row["checklist"])  # type: ignore[index]
                except Exception:
                    pass
            if deps_map.get(row["id"]):
                task["depends_on"] = deps_map[row["id"]]
            tasks.append(task)

        return {"metadata": {"exported": _utcnow_iso()}, "tasks": tasks}

    def export_snapshot_to_json(self, out_path: Path) -> None:
        """Write a snapshot of tasks to a JSON file for UI compatibility."""
        try:
            payload = self.export_tasks_json()
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with open(out_path, "w") as f:
                json.dump(payload, f, indent=2)
        except Exception:
            # Snapshot is best-effort; do not raise
            pass

    # ------------------------------
    # Core operations
    # ------------------------------

    def get_task(self, task_id: str) -> Optional[dict[str, Any]]:
        with self.connect() as conn:
            row = conn.execute("select * from tasks where id=?", (task_id,)).fetchone()
        return dict(row) if row else None

    def list_tasks(self, *, status: Optional[str] = None, course: Optional[str] = None) -> list[dict[str, Any]]:
        query = "select * from tasks"
        params: list[Any] = []
        clauses: list[str] = []
        if status:
            clauses.append("status=?")
            params.append(status)
        if course:
            clauses.append("course=?")
            params.append(course)
        if clauses:
            query += " where " + " and ".join(clauses)
        with self.connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def update_task_field(self, task_id: str, field: str, value: Any) -> bool:
        allowed = {
            "status",
            "title",
            "due_at",
            "est_minutes",
            "weight",
            "category",
            "notes",
        }
        if field not in allowed:
            return False
        with self.connect() as conn:
            cur = conn.execute(
                f"update tasks set {field}=?, updated_at=? where id=?",
                (value, _utcnow_iso(), task_id),
            )
        return cur.rowcount > 0

    def update_task_fields(self, task_id: str, updates: dict[str, Any]) -> bool:
        """Update multiple allowed fields; returns True if any row updated."""
        allowed = [
            "status",
            "title",
            "due_at",
            "est_minutes",
            "weight",
            "category",
            "notes",
        ]
        set_parts = []
        params: list[Any] = []
        for k, v in updates.items():
            if k in allowed:
                set_parts.append(f"{k}=?")
                params.append(v)
        if not set_parts:
            return False
        set_sql = ", ".join(set_parts) + ", updated_at=?"
        params.append(_utcnow_iso())
        params.append(task_id)
        with self.connect() as conn:
            cur = conn.execute(f"update tasks set {set_sql} where id=?", params)
        return cur.rowcount > 0

    def create_task(self, task: dict[str, Any]) -> str:
        """Create a task; returns id. Expects id or generates one if missing."""
        tid = task.get("id")
        if not tid:
            # simple local id gen: COURSE-<timestamp>
            from datetime import datetime

            course = (task.get("course") or "GEN").upper()
            tid = f"{course}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        now = _utcnow_iso()
        fields = {
            "id": tid,
            "course": task.get("course"),
            "title": task.get("title") or "",
            "status": task.get("status") or "todo",
            "due_at": task.get("due_at") or task.get("due_date"),
            "est_minutes": task.get("est_minutes"),
            "weight": float(task.get("weight", 1.0)),
            "category": task.get("category"),
            "anchor": 1 if task.get("anchor") else 0,
            "notes": task.get("notes") or task.get("description"),
            "created_at": task.get("created_at") or now,
            "updated_at": task.get("updated_at") or now,
        }
        with self.connect() as conn:
            conn.execute(
                """
                insert into tasks(id, course, title, status, due_at, est_minutes, weight, category, anchor, notes, created_at, updated_at)
                values(:id, :course, :title, :status, :due_at, :est_minutes, :weight, :category, :anchor, :notes, :created_at, :updated_at)
                """,
                fields,
            )
        # deps
        deps = task.get("depends_on") or []
        if deps:
            self.add_deps(tid, deps)
        return tid

    def add_deps(self, task_id: str, depends_on: Iterable[str]) -> None:
        with self.connect() as conn:
            for dep_id in depends_on:
                conn.execute("insert or ignore into deps(task_id, blocks_id) values(?, ?)", (task_id, dep_id))

    def remove_from_now_queue(self, task_id: str) -> None:
        with self.connect() as conn:
            rows = conn.execute("select pos, task_id from now_queue order by pos").fetchall()
            kept = [r["task_id"] for r in rows if r["task_id"] != task_id]
        self.set_now_queue(kept)

    def add_event(self, task_id: str, field: str, from_val: Optional[str], to_val: Optional[str]) -> None:
        with self.connect() as conn:
            conn.execute(
                "insert into events(at, task_id, field, from_val, to_val) values(?,?,?,?,?)",
                (_utcnow_iso(), task_id, field, from_val, to_val),
            )

    def upsert_score(self, task_id: str, score: float, factors: dict[str, Any]) -> None:
        with self.connect() as conn:
            conn.execute(
                "insert into scores(task_id, score, factors, computed_at) values(?,?,?,?)\n                 on conflict(task_id) do update set score=excluded.score, factors=excluded.factors, computed_at=excluded.computed_at",
                (task_id, float(score), json.dumps(factors), _utcnow_iso()),
            )

    def get_score(self, task_id: str) -> Optional[dict[str, Any]]:
        with self.connect() as conn:
            row = conn.execute("select * from scores where task_id=?", (task_id,)).fetchone()
        return dict(row) if row else None

    # Now queue operations
    def get_now_queue(self) -> list[str]:
        with self.connect() as conn:
            rows = conn.execute("select task_id from now_queue order by pos").fetchall()
        return [r["task_id"] for r in rows]

    def set_now_queue(self, task_ids: Iterable[str]) -> None:
        with self.connect() as conn:
            conn.execute("delete from now_queue")
            for i, tid in enumerate(task_ids, start=1):
                conn.execute("insert into now_queue(pos, task_id) values(?,?)", (i, tid))

    # Health
    def health(self) -> dict[str, Any]:
        with self.connect() as conn:
            try:
                n_tasks = conn.execute("select count(*) from tasks").fetchone()[0]
                n_events = conn.execute("select count(*) from events").fetchone()[0]
                return {"ok": True, "tasks": int(n_tasks), "events": int(n_events)}
            except sqlite3.DatabaseError as exc:  # pragma: no cover - unexpected
                return {"ok": False, "error": str(exc)}

    # ------------------------------
    # Deletions and bulk updates
    # ------------------------------

    def delete_task(self, task_id: str) -> bool:
        """Delete a task and any queue references. Returns True if deleted."""
        with self.connect() as conn:
            # Remove from now_queue first to keep consistency
            conn.execute("delete from now_queue where task_id=?", (task_id,))
            cur = conn.execute("delete from tasks where id=?", (task_id,))
        return cur.rowcount > 0

    def reset_all_statuses(self, status: str = "todo") -> int:
        """Set status for all tasks and return affected row count."""
        if status not in {"todo", "doing", "review", "done", "blocked"}:
            raise ValueError("Invalid status value")
        with self.connect() as conn:
            cur = conn.execute("update tasks set status=?, updated_at=?", (status, _utcnow_iso()))
        return int(cur.rowcount)
