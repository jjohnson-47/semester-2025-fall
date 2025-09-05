"""
Integration tests for course projection workflow
Tests the V2 architecture with course registry and projections
"""

import pytest
import sqlite3
import json
from pathlib import Path
import tempfile
import shutil


class TestCourseProjectionWorkflow:
    """Test the complete course projection workflow"""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = Path(f.name)
        
        # Initialize tables
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create course_registry table
        cursor.execute("""
            CREATE TABLE course_registry (
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
        
        # Create course_projection table
        cursor.execute("""
            CREATE TABLE course_projection (
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
        
        conn.commit()
        conn.close()
        
        yield db_path
        
        # Cleanup
        db_path.unlink(missing_ok=True)
    
    def test_course_registration(self, temp_db):
        """Test registering a new course"""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # Register a course
        cursor.execute("""
            INSERT INTO course_registry 
            (course_code, title, credits, instructor, schedule, 
             location, start_date, end_date, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        """, (
            "TEST101",
            "Test Course",
            3,
            "Dr. Test",
            "MWF 10:00-11:00",
            "Room 101",
            "2025-08-25",
            "2025-12-13"
        ))
        
        conn.commit()
        
        # Verify registration
        cursor.execute("SELECT * FROM course_registry WHERE course_code = ?", ("TEST101",))
        result = cursor.fetchone()
        
        assert result is not None
        assert result[0] == "TEST101"  # course_code
        assert result[1] == "Test Course"  # title
        assert result[2] == 3  # credits
        
        conn.close()
    
    def test_projection_creation(self, temp_db):
        """Test creating course projections"""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # First register the course
        cursor.execute("""
            INSERT INTO course_registry 
            (course_code, title, credits, instructor, schedule, 
             location, start_date, end_date, created_at, updated_at)
            VALUES ('TEST102', 'Test Course 2', 3, 'Dr. Test', 'TTh 2:00-3:30',
                    'Room 102', '2025-08-25', '2025-12-13', 
                    datetime('now'), datetime('now'))
        """)
        
        # Create syllabus projection
        syllabus_data = {
            "course_title": "Test Course 2",
            "credits": 3,
            "instructor": {"name": "Dr. Test", "email": "test@example.com"},
            "grading_scale": {"A": 90, "B": 80, "C": 70, "D": 60, "F": 0}
        }
        
        cursor.execute("""
            INSERT INTO course_projection
            (course_code, projection_type, projection_data, 
             version, created_at, updated_at)
            VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))
        """, (
            "TEST102",
            "syllabus",
            json.dumps(syllabus_data),
            1
        ))
        
        conn.commit()
        
        # Verify projection
        cursor.execute("""
            SELECT projection_type, projection_data 
            FROM course_projection 
            WHERE course_code = ?
        """, ("TEST102",))
        
        result = cursor.fetchone()
        assert result is not None
        assert result[0] == "syllabus"
        
        data = json.loads(result[1])
        assert data["course_title"] == "Test Course 2"
        assert data["credits"] == 3
        
        conn.close()
    
    def test_projection_uniqueness(self, temp_db):
        """Test that projection types are unique per course"""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # Register course
        cursor.execute("""
            INSERT INTO course_registry 
            (course_code, title, credits, instructor, schedule, 
             location, start_date, end_date, created_at, updated_at)
            VALUES ('TEST103', 'Test Course 3', 3, 'Dr. Test', 'MWF 1:00-2:00',
                    'Room 103', '2025-08-25', '2025-12-13',
                    datetime('now'), datetime('now'))
        """)
        
        # Create first projection
        cursor.execute("""
            INSERT INTO course_projection
            (course_code, projection_type, projection_data, 
             version, created_at, updated_at)
            VALUES ('TEST103', 'schedule', '{}', 1, 
                    datetime('now'), datetime('now'))
        """)
        
        conn.commit()
        
        # Try to create duplicate (should use INSERT OR REPLACE in real code)
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO course_projection
                (course_code, projection_type, projection_data, 
                 version, created_at, updated_at)
                VALUES ('TEST103', 'schedule', '{"updated": true}', 1,
                        datetime('now'), datetime('now'))
            """)
        
        conn.close()
    
    def test_full_workflow(self, temp_db):
        """Test the complete workflow from registration to projection retrieval"""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # 1. Register multiple courses
        courses = [
            ("MATH201", "Calculus I", 4, "Dr. Math"),
            ("STAT201", "Statistics I", 3, "Dr. Stats"),
            ("COMP201", "Intro to Programming", 3, "Dr. Comp")
        ]
        
        for code, title, credits, instructor in courses:
            cursor.execute("""
                INSERT INTO course_registry 
                (course_code, title, credits, instructor, schedule, 
                 location, start_date, end_date, created_at, updated_at)
                VALUES (?, ?, ?, ?, 'TBD', 'TBD', '2025-08-25', '2025-12-13',
                        datetime('now'), datetime('now'))
            """, (code, title, credits, instructor))
        
        # 2. Create projections for each course
        for code, title, credits, instructor in courses:
            # Syllabus projection
            syllabus = {
                "course_code": code,
                "course_title": title,
                "credits": credits,
                "instructor": {"name": instructor}
            }
            cursor.execute("""
                INSERT INTO course_projection
                (course_code, projection_type, projection_data, 
                 version, created_at, updated_at)
                VALUES (?, 'syllabus', ?, 1, datetime('now'), datetime('now'))
            """, (code, json.dumps(syllabus)))
            
            # Schedule projection
            schedule = {
                "weeks": [f"Week {i+1}" for i in range(15)],
                "course_code": code
            }
            cursor.execute("""
                INSERT INTO course_projection
                (course_code, projection_type, projection_data, 
                 version, created_at, updated_at)
                VALUES (?, 'schedule', ?, 1, datetime('now'), datetime('now'))
            """, (code, json.dumps(schedule)))
        
        conn.commit()
        
        # 3. Query all courses with their projections
        cursor.execute("""
            SELECT 
                r.course_code,
                r.title,
                COUNT(p.id) as projection_count
            FROM course_registry r
            LEFT JOIN course_projection p ON r.course_code = p.course_code
            GROUP BY r.course_code, r.title
        """)
        
        results = cursor.fetchall()
        assert len(results) == 3
        
        for result in results:
            code, title, proj_count = result
            assert proj_count == 2  # Each course should have 2 projections
        
        # 4. Verify we can retrieve specific projections
        cursor.execute("""
            SELECT projection_data 
            FROM course_projection 
            WHERE course_code = ? AND projection_type = ?
        """, ("MATH201", "syllabus"))
        
        result = cursor.fetchone()
        assert result is not None
        
        data = json.loads(result[0])
        assert data["course_title"] == "Calculus I"
        assert data["credits"] == 4
        
        conn.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])