#!/usr/bin/env python3
"""
Migration 003: Add performance indexes for hot columns
Creates indexes on frequently queried columns for optimal performance
"""

import sqlite3
from pathlib import Path


def up(conn: sqlite3.Connection):
    """Add performance indexes to tasks table"""
    cursor = conn.cursor()

    # Get existing indexes
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='index' AND tbl_name='tasks'
    """)
    existing_indexes = [idx[0] for idx in cursor.fetchall()]

    # Define indexes to create
    indexes = [
        ("idx_tasks_status", "status", "Task status queries"),
        ("idx_tasks_course", "course", "Course filtering"),
        ("idx_tasks_due_at", "due_at", "Date-based queries"),
        ("idx_tasks_category", "category", "Category filtering"),
        ("idx_tasks_composite", "course, status, due_at", "Composite queries"),
        ("idx_tasks_anchor", "anchor", "Anchor task lookups"),
    ]

    created_count = 0
    for idx_name, columns, description in indexes:
        if idx_name not in existing_indexes:
            try:
                cursor.execute(f"""
                    CREATE INDEX {idx_name} 
                    ON tasks({columns})
                """)
                print(f"✓ Created index {idx_name} - {description}")
                created_count += 1
            except sqlite3.OperationalError as e:
                print(f"  Index {idx_name} may already exist: {e}")
        else:
            print(f"  Index {idx_name} already exists")

    # Also ensure course_projection indexes exist
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_projection_type_course 
        ON course_projection(projection_type, course_code)
    """)
    print("✓ Ensured course_projection composite index")

    # Analyze tables to update statistics
    cursor.execute("ANALYZE tasks")
    cursor.execute("ANALYZE course_projection")
    cursor.execute("ANALYZE course_registry")
    print("✓ Updated table statistics with ANALYZE")

    conn.commit()

    return created_count


def benchmark_queries(conn: sqlite3.Connection):
    """Run sample queries to verify index usage"""
    cursor = conn.cursor()

    print("\nBenchmarking indexed queries:")
    print("-" * 50)

    # Test queries that should use indexes
    test_queries = [
        ("Status filter", "SELECT COUNT(*) FROM tasks WHERE status = 'pending'"),
        ("Course filter", "SELECT COUNT(*) FROM tasks WHERE course = 'MATH221'"),
        (
            "Due date range",
            "SELECT COUNT(*) FROM tasks WHERE due_at BETWEEN '2025-09-01' AND '2025-09-30'",
        ),
        (
            "Composite query",
            "SELECT * FROM tasks WHERE course = 'MATH251' AND status = 'pending' ORDER BY due_at LIMIT 10",
        ),
        ("Origin lookup", "SELECT COUNT(*) FROM tasks WHERE origin_kind = 'course'"),
    ]

    for description, query in test_queries:
        # Use EXPLAIN QUERY PLAN to verify index usage
        explain_query = f"EXPLAIN QUERY PLAN {query}"
        cursor.execute(explain_query)
        plan = cursor.fetchall()

        # Check if index is being used
        uses_index = any("USING INDEX" in str(row) for row in plan)
        status = "✓ Uses index" if uses_index else "⚠ Table scan"

        print(f"  {description:20} {status}")
        if not uses_index:
            print(f"    Plan: {plan}")


def main():
    """Run migration"""
    db_path = Path("dashboard/state/tasks.db")

    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        return 1

    conn = sqlite3.connect(db_path)

    try:
        print("Migration 003: Adding performance indexes")
        print("=" * 50)

        # Run migration
        created = up(conn)

        # Benchmark to verify
        benchmark_queries(conn)

        # Report statistics
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as index_count
            FROM sqlite_master 
            WHERE type='index' AND tbl_name='tasks'
        """)
        total_indexes = cursor.fetchone()[0]

        print("\n" + "=" * 50)
        print("✓ Migration complete")
        print(f"  Indexes created: {created}")
        print(f"  Total indexes on tasks table: {total_indexes}")

        # Check database size impact
        cursor.execute(
            "SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()"
        )
        db_size = cursor.fetchone()[0]
        print(f"  Database size: {db_size:,} bytes")

        return 0

    except Exception as e:
        print(f"Migration failed: {e}")
        return 1

    finally:
        conn.close()


if __name__ == "__main__":
    exit(main())
