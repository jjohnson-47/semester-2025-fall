#!/bin/bash
# Interactive secrets creation helper

echo "📝 Creating .env.secrets file interactively..."
echo

# Flask secret key
echo "Flask Secret Key (leave blank to auto-generate):"
read -p "> " flask_key
if [ -z "$flask_key" ]; then
    flask_key=$(python -c "import secrets; print(secrets.token_hex(32))")
    echo "Generated: ${flask_key:0:10}..."
fi

# Course credentials
echo -e "\nMyOpenMath Course ID [292612]:"
read -p "> " myopen_id
myopen_id=${myopen_id:-292612}

echo "MyOpenMath Enrollment Key [math221fall2025]:"
read -p "> " myopen_key
myopen_key=${myopen_key:-math221fall2025}

echo "Edfinity Registration Code [H7C84FUR]:"
read -p "> " edfinity_code
edfinity_code=${edfinity_code:-H7C84FUR}

# Write to file
cat > .env.secrets << EOF
# Sensitive environment variables
# DO NOT COMMIT THIS FILE
# Generated: $(date)

# Flask security
FLASK_SECRET_KEY=$flask_key

# Course platform credentials
MYOPENMATH_COURSE_ID=$myopen_id
MYOPENMATH_ENROLLMENT_KEY=$myopen_key
EDFINITY_REGISTRATION_CODE=$edfinity_code

# Future: API credentials
# BLACKBOARD_API_KEY=
# BLACKBOARD_API_SECRET=
EOF

echo -e "\n✅ Created .env.secrets"

# Offer to encrypt
if command -v age &> /dev/null && [ -f ~/.config/age/keys.txt ]; then
    echo -e "\nWould you like to encrypt this file for safe storage? (y/n)"
    read -p "> " encrypt
    if [ "$encrypt" = "y" ]; then
        age -e -i ~/.config/age/keys.txt -o .env.secrets.age .env.secrets
        echo "✅ Created encrypted .env.secrets.age (safe to commit)"
    fi
fi
