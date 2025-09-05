#!/usr/bin/env python3
"""
Migration 002: Add origin tracking columns to tasks table
Adds origin_ref, origin_kind, and origin_version columns for tracking task origins
"""

import sqlite3
from pathlib import Path


def up(conn: sqlite3.Connection):
    """Add origin tracking columns to tasks table"""
    cursor = conn.cursor()

    # Check if columns already exist
    cursor.execute("PRAGMA table_info(tasks)")
    existing_columns = [col[1] for col in cursor.fetchall()]

    # Add origin_ref column if it doesn't exist
    if "origin_ref" not in existing_columns:
        cursor.execute("""
            ALTER TABLE tasks 
            ADD COLUMN origin_ref TEXT
        """)
        print("✓ Added origin_ref column to tasks table")
    else:
        print("  origin_ref column already exists")

    # Add origin_kind column if it doesn't exist
    if "origin_kind" not in existing_columns:
        cursor.execute("""
            ALTER TABLE tasks 
            ADD COLUMN origin_kind TEXT
        """)
        print("✓ Added origin_kind column to tasks table")
    else:
        print("  origin_kind column already exists")

    # Add origin_version column if it doesn't exist
    if "origin_version" not in existing_columns:
        cursor.execute("""
            ALTER TABLE tasks 
            ADD COLUMN origin_version INTEGER DEFAULT 1
        """)
        print("✓ Added origin_version column to tasks table")
    else:
        print("  origin_version column already exists")

    # Create index on origin columns for efficient querying
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_tasks_origin 
        ON tasks(origin_kind, origin_ref)
    """)
    print("✓ Created index on origin columns")

    conn.commit()


def down(conn: sqlite3.Connection):
    """Remove origin tracking columns from tasks table"""
    # SQLite doesn't support dropping columns directly
    # Would need to recreate table without these columns
    _ = conn  # Unused but required for interface
    print("⚠ SQLite doesn't support dropping columns. Manual intervention required.")


def populate_origin_data(conn: sqlite3.Connection):
    """Populate origin data for existing tasks based on patterns"""
    cursor = conn.cursor()

    # Update tasks with discernible patterns
    updates = []

    # Course-based tasks
    cursor.execute("""
        UPDATE tasks 
        SET origin_kind = 'course', 
            origin_ref = course,
            origin_version = 1
        WHERE origin_kind IS NULL 
        AND course IS NOT NULL
    """)
    updates.append(f"Set origin for {cursor.rowcount} course-based tasks")

    # Blackboard tasks
    cursor.execute("""
        UPDATE tasks 
        SET origin_kind = 'blackboard',
            origin_version = 1
        WHERE origin_kind IS NULL 
        AND (title LIKE '%Blackboard%' OR category = 'Blackboard Setup')
    """)
    updates.append(f"Set origin for {cursor.rowcount} Blackboard tasks")

    # Assessment tasks
    cursor.execute("""
        UPDATE tasks 
        SET origin_kind = 'assessment',
            origin_version = 1
        WHERE origin_kind IS NULL 
        AND category = 'assessment'
    """)
    updates.append(f"Set origin for {cursor.rowcount} assessment tasks")

    conn.commit()

    for update in updates:
        print(f"  {update}")

    # Report on any tasks without origin
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE origin_kind IS NULL")
    untracked = cursor.fetchone()[0]
    if untracked > 0:
        print(f"  ⚠ {untracked} tasks remain without origin tracking")


def main():
    """Run migration"""
    db_path = Path("dashboard/state/tasks.db")

    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        return 1

    conn = sqlite3.connect(db_path)

    try:
        print("Migration 002: Adding origin tracking columns")
        print("-" * 50)

        # Run migration
        up(conn)

        # Populate origin data
        print("\nPopulating origin data:")
        populate_origin_data(conn)

        # Verify
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(tasks)")
        columns = [col[1] for col in cursor.fetchall()]

        origin_cols = ["origin_ref", "origin_kind", "origin_version"]
        all_present = all(col in columns for col in origin_cols)

        if all_present:
            print("\n✓ Migration complete: All origin tracking columns added")

            # Statistics
            cursor.execute("SELECT COUNT(*) FROM tasks WHERE origin_kind IS NOT NULL")
            tracked = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM tasks")
            total = cursor.fetchone()[0]

            print(f"  Origin tracking: {tracked}/{total} tasks")
        else:
            print("\n✗ Migration incomplete: Some columns missing")
            return 1

        return 0

    except Exception as e:
        print(f"Migration failed: {e}")
        return 1

    finally:
        conn.close()


if __name__ == "__main__":
    exit(main())
