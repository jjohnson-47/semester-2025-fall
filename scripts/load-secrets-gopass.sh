#!/bin/bash
# Load secrets from gopass into environment

if ! command -v gopass &> /dev/null; then
    echo "❌ gopass not found"
    return 1
fi

# Flask secret
if gopass show development/jjohnson-47/flask-secret-key &> /dev/null 2>&1; then
    export FLASK_SECRET_KEY=$(gopass show -o development/jjohnson-47/flask-secret-key)
fi

# Course platforms
if gopass show development/jjohnson-47/myopenmath/course-id &> /dev/null 2>&1; then
    export MYOPENMATH_COURSE_ID=$(gopass show -o development/jjohnson-47/myopenmath/course-id)
    export MYOPENMATH_ENROLLMENT_KEY=$(gopass show -o development/jjohnson-47/myopenmath/enrollment-key)
fi

if gopass show development/jjohnson-47/edfinity/registration-code &> /dev/null 2>&1; then
    export EDFINITY_REGISTRATION_CODE=$(gopass show -o development/jjohnson-47/edfinity/registration-code)
fi

echo "✅ Secrets loaded from gopass"