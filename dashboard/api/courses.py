#!/usr/bin/env python3
"""
Course API endpoints.
"""

from flask import jsonify
from flask.typing import ResponseReturnValue

from dashboard.api import api_bp


@api_bp.route("/courses", methods=["GET"])
def get_courses() -> ResponseReturnValue:
    """Get list of all courses."""
    # For now, return static course list
    courses = [
        {
            "code": "MATH221",
            "name": "Calculus I",
            "instructor": "TBD",
            "credits": 4,
            "students": 30,
        },
        {
            "code": "MATH251",
            "name": "Calculus II",
            "instructor": "TBD",
            "credits": 4,
            "students": 25,
        },
        {
            "code": "STAT253",
            "name": "Applied Statistics",
            "instructor": "TBD",
            "credits": 3,
            "students": 35,
        },
    ]

    return jsonify({"courses": courses, "total": len(courses)})


@api_bp.route("/courses/<course_code>", methods=["GET"])
def get_course(course_code: str) -> ResponseReturnValue:
    """Get details for a specific course."""
    courses = {
        "MATH221": {
            "code": "MATH221",
            "name": "Calculus I",
            "description": "Introduction to differential and integral calculus",
            "instructor": "TBD",
            "credits": 4,
            "meeting_times": "MWF 10:00-11:00",
            "location": "Science Building 101",
            "students": 30,
        },
        "MATH251": {
            "code": "MATH251",
            "name": "Calculus II",
            "description": "Continuation of Calculus I",
            "instructor": "TBD",
            "credits": 4,
            "meeting_times": "TTh 2:00-3:30",
            "location": "Science Building 102",
            "students": 25,
        },
        "STAT253": {
            "code": "STAT253",
            "name": "Applied Statistics",
            "description": "Statistical methods and applications",
            "instructor": "TBD",
            "credits": 3,
            "meeting_times": "MWF 1:00-2:00",
            "location": "Math Building 201",
            "students": 35,
        },
    }

    course = courses.get(course_code.upper())
    if not course:
        return jsonify({"error": "Course not found"}), 404

    return jsonify(course)
