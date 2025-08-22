#!/bin/bash
# Universal development environment setup

set -e

echo "🚀 Setting up development environment..."

# Detect OS and environment
if grep -q Microsoft /proc/version 2>/dev/null; then
    ENV_TYPE="wsl"
    echo "📍 Detected: WSL environment"
else
    ENV_TYPE="native"
    echo "📍 Detected: Native Linux"
fi

# Check for required tools
check_tool() {
    if ! command -v $1 &> /dev/null; then
        echo "❌ $1 is not installed"
        return 1
    fi
    echo "✅ $1 found"
    return 0
}

echo -e "\n📋 Checking dependencies..."
check_tool python3
check_tool uv
check_tool git
check_tool age || echo "  ⚠️  Optional: Install age for secrets management"
check_tool gopass || echo "  ⚠️  Optional: Install gopass for advanced secrets"

# Setup Python environment
echo -e "\n🐍 Setting up Python environment..."
if [ ! -d ".venv" ]; then
    uv venv
fi
uv sync --all-extras --dev

# Setup environment files
echo -e "\n🔐 Setting up environment configuration..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "📝 Created .env from template"
fi

# Handle secrets based on available tools
if command -v gopass &> /dev/null && gopass ls &> /dev/null 2>&1; then
    echo "🔑 Loading secrets from gopass..."
    source scripts/load-secrets-gopass.sh
elif [ -f ".env.secrets.age" ] && command -v age &> /dev/null; then
    echo "🔓 Decrypting secrets file..."
    age -d -i ~/.config/age/keys.txt .env.secrets.age > .env.secrets
    source .env.secrets
elif [ -f ".env.secrets" ]; then
    echo "📂 Loading local secrets file..."
    source .env.secrets
else
    echo "⚠️  No secrets configuration found"
    echo "   Run: scripts/init-secrets.sh"
fi

# Create required directories
echo -e "\n📁 Creating project directories..."
mkdir -p build dashboard/state content/courses

# WSL-specific adjustments
if [ "$ENV_TYPE" = "wsl" ]; then
    echo -e "\n🪟 Applying WSL-specific configurations..."
    # Fix line endings
    git config core.autocrlf input
    # Ensure proper permissions
    find scripts -type f -name "*.sh" -exec chmod +x {} \;
fi

echo -e "\n✨ Development environment ready!"
echo "   Run: source .venv/bin/activate"
echo "   Then: make validate"