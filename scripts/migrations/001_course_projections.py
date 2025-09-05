#!/usr/bin/env python3
"""
Migration 001: Create course projection tables
Creates course_registry and course_projection tables for V2 architecture
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path


def up(conn: sqlite3.Connection):
    """Create course projection tables"""
    cursor = conn.cursor()
    
    # Create course_registry table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS course_registry (
            course_code TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            credits INTEGER NOT NULL,
            instructor TEXT,
            schedule TEXT,
            location TEXT,
            start_date TEXT,
            end_date TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    
    # Create course_projection table for denormalized view
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS course_projection (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_code TEXT NOT NULL,
            projection_type TEXT NOT NULL,
            projection_data TEXT NOT NULL,
            version INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (course_code) REFERENCES course_registry(course_code),
            UNIQUE(course_code, projection_type)
        )
    """)
    
    # Create indexes
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_projection_course 
        ON course_projection(course_code)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_projection_type 
        ON course_projection(projection_type)
    """)
    
    conn.commit()
    print("✓ Created course_registry and course_projection tables")


def down(conn: sqlite3.Connection):
    """Drop course projection tables"""
    cursor = conn.cursor()
    
    cursor.execute("DROP TABLE IF EXISTS course_projection")
    cursor.execute("DROP TABLE IF EXISTS course_registry")
    
    conn.commit()
    print("✓ Dropped course projection tables")


def populate_from_courses(conn: sqlite3.Connection):
    """Populate tables from existing course data"""
    cursor = conn.cursor()
    
    # Load course data
    courses_dir = Path("content/courses")
    courses_added = []
    
    for course_dir in courses_dir.iterdir():
        if course_dir.is_dir():
            course_code = course_dir.name
            
            # Aggregate course data from multiple JSON files
            course_data = {}
            for json_file in course_dir.glob("*.json"):
                with open(json_file) as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        course_data.update(data)
            
            if course_data:
                # Extract metadata for registry
                title = course_data.get("course_title", f"{course_code} Course")
                credits = course_data.get("credits", 3)
                instructor = course_data.get("instructor", {})
                if isinstance(instructor, dict):
                    instructor_name = instructor.get("name", "TBD")
                else:
                    instructor_name = str(instructor) if instructor else "TBD"
                
                meeting_times = course_data.get("meeting_times", "")
                if isinstance(meeting_times, list):
                    meeting_times = ", ".join(meeting_times)
                
                location = course_data.get("location", "TBD")
                
                # Insert into course_registry
                cursor.execute("""
                    INSERT OR REPLACE INTO course_registry 
                    (course_code, title, credits, instructor, schedule, 
                     location, start_date, end_date, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    course_code,
                    title,
                    credits,
                    instructor_name,
                    meeting_times,
                    location,
                    "2025-08-25",  # Fall 2025 start
                    "2025-12-13",  # Fall 2025 end
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
                
                # Create combined syllabus projection
                cursor.execute("""
                    INSERT OR REPLACE INTO course_projection
                    (course_code, projection_type, projection_data, 
                     version, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    course_code,
                    "syllabus",
                    json.dumps(course_data),
                    1,
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
                
                courses_added.append(course_code)
            
            # Check for schedule-specific data
            schedule_file = course_dir / "schedule.json"
            if schedule_file.exists():
                with open(schedule_file) as f:
                    schedule = json.load(f)
                
                cursor.execute("""
                    INSERT OR REPLACE INTO course_projection
                    (course_code, projection_type, projection_data,
                     version, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    course_code,
                    "schedule",
                    json.dumps(schedule),
                    1,
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
    
    conn.commit()
    print(f"✓ Populated data for courses: {', '.join(courses_added)}")
    return courses_added


def main():
    """Run migration"""
    db_path = Path("dashboard/state/tasks.db")
    
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        return 1
    
    conn = sqlite3.connect(db_path)
    
    try:
        # Run migration
        up(conn)
        
        # Populate data
        populate_from_courses(conn)
        
        # Verify
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM course_registry")
        reg_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM course_projection")
        proj_count = cursor.fetchone()[0]
        
        print("\nMigration complete:")
        print(f"  - course_registry: {reg_count} records")
        print(f"  - course_projection: {proj_count} records")
        
        return 0
        
    except Exception as e:
        print(f"Migration failed: {e}")
        down(conn)  # Rollback
        return 1
        
    finally:
        conn.close()


if __name__ == "__main__":
    exit(main())