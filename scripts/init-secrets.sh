#!/bin/bash
# Initialize secrets for new development machine

set -e

echo "🔐 Initializing Secrets Management"
echo "=================================="
echo
echo "Choose your setup method:"
echo "1) Gopass with GitHub sync (recommended)"
echo "2) Local encrypted file with age"
echo "3) Manual .env.secrets file"
echo
read -p "Select option (1-3): " choice

case $choice in
    1)
        echo -e "\n📦 Setting up gopass..."
        
        # Check gopass installation
        if ! command -v gopass &> /dev/null; then
            echo "Installing gopass..."
            sudo dnf install -y gopass age || sudo apt-get install -y gopass age
        fi
        
        # Clone store
        read -p "Enter your GitHub username [verlyn13]: " github_user
        github_user=${github_user:-verlyn13}
        
        echo "Cloning gopass store..."
        git clone git@github.com:${github_user}/gopass-secrets.git ~/.local/share/gopass/stores/root
        
        echo "⚠️  You need to transfer your age key from primary machine:"
        echo "   Run on primary machine: ./scripts/transfer-age-key.sh"
        echo "   This will guide you through secure transfer options"
        echo
        read -p "Press Enter when age key is in ~/.config/age/keys.txt..."
        
        gopass init --store root
        ./scripts/setup-gopass-secrets.sh
        ;;
        
    2)
        echo -e "\n🔓 Setting up age encryption..."
        
        if ! command -v age &> /dev/null; then
            echo "Installing age..."
            sudo dnf install -y age || sudo apt-get install -y age
        fi
        
        if [ ! -f ~/.config/age/keys.txt ]; then
            echo "Generating age keypair..."
            mkdir -p ~/.config/age
            age-keygen -o ~/.config/age/keys.txt
            echo "⚠️  BACKUP THIS KEY: ~/.config/age/keys.txt"
        fi
        
        if [ -f .env.secrets.age ]; then
            echo "Decrypting existing secrets..."
            age -d -i ~/.config/age/keys.txt .env.secrets.age > .env.secrets
        else
            echo "Creating new secrets file..."
            ./scripts/create-secrets-interactive.sh
        fi
        ;;
        
    3)
        echo -e "\n📝 Manual setup..."
        if [ ! -f .env.secrets ]; then
            cat > .env.secrets << 'EOF'
# Sensitive environment variables
# DO NOT COMMIT THIS FILE

# Generate with: python -c "import secrets; print(secrets.token_hex(32))"
FLASK_SECRET_KEY=your-secret-key-here

# Course platform credentials
MYOPENMATH_COURSE_ID=292612
MYOPENMATH_ENROLLMENT_KEY=math221fall2025
EDFINITY_REGISTRATION_CODE=H7C84FUR

# Future: API credentials
# BLACKBOARD_API_KEY=
# BLACKBOARD_API_SECRET=
EOF
            echo "Created .env.secrets template"
            echo "⚠️  Edit .env.secrets with actual values"
        fi
        ;;
esac

echo -e "\n✅ Secrets initialization complete!"