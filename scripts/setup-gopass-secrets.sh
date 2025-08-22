#!/bin/bash
# Setup project secrets in gopass

set -e

echo "🔑 Setting up project secrets in gopass..."

# Check if secrets already exist
check_secret() {
    gopass show $1 &> /dev/null && echo "exists" || echo "missing"
}

# Flask secret key
if [ "$(check_secret development/jjohnson-47/flask-secret-key)" = "missing" ]; then
    echo "Generating Flask secret key..."
    python -c "import secrets; print(secrets.token_hex(32))" | \
        gopass insert -f development/jjohnson-47/flask-secret-key
fi

# Course credentials
if [ "$(check_secret development/jjohnson-47/myopenmath/course-id)" = "missing" ]; then
    echo "Setting up MyOpenMath credentials..."
    echo "292612" | gopass insert -f development/jjohnson-47/myopenmath/course-id
    echo "math221fall2025" | gopass insert -f development/jjohnson-47/myopenmath/enrollment-key
fi

if [ "$(check_secret development/jjohnson-47/edfinity/registration-code)" = "missing" ]; then
    echo "Setting up Edfinity credentials..."
    echo "H7C84FUR" | gopass insert -f development/jjohnson-47/edfinity/registration-code
fi

echo "✅ Secrets configured in gopass"
