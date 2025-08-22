# Secrets and Environment Variables Audit Report

## Fall 2025 Semester Project

### Current State

#### 1. Environment Variables in Use

- **Configuration File**: `.env` (active), `.env.example` (template)
- **Non-sensitive settings** currently stored:
  - Semester information (code, name, timezone)
  - Institution details (KPC, UAA)
  - Instructor information (name, email, office, phone)
  - Course names and descriptions
  - Build settings (PDF, DOCX generation flags)
  - Dashboard settings (port, host)
  - File paths and directories

#### 2. Secrets Found in Codebase

##### Dashboard Application

- **Flask SECRET_KEY**: Currently using default `"dev-key-change-in-production"`
  - Location: `dashboard/config.py:13`
  - **SECURITY RISK**: Needs proper secret for production

##### GitHub Actions

- Using standard GitHub secrets:
  - `GITHUB_TOKEN` (provided by GitHub)
  - `CODECOV_TOKEN` (for code coverage - optional)

##### Course Platform Credentials

- **MyOpenMath (MATH221)**:
  - Course ID: `292612` (public)
  - Enrollment Key: `math221fall2025` (semi-public, stored in JSON)

- **Edfinity (MATH251)**:
  - Registration Link: `https://edfinity.com/join/H7C84FUR` (contains access code)

- **Pearson MyLab (STAT253)**:
  - Integrated with Blackboard (no separate credentials stored)

### Security Assessment

#### ✅ Good Practices Found

1. Using `.env` file for configuration (gitignored)
2. Providing `.env.example` template without sensitive data
3. GitHub Actions using built-in secrets management
4. No hardcoded API keys or passwords in Python code

#### ⚠️ Issues Requiring Attention

1. **Flask SECRET_KEY**: Currently using insecure default
2. **Course enrollment keys**: Stored in plain text JSON files
3. **No gopass integration**: Your gopass setup isn't being utilized
4. **Missing secrets**: No API keys for potential integrations

### Recommended Secrets Management Strategy

#### 1. Immediate Actions

##### A. Flask Secret Key

```bash
# Generate and store in gopass
python -c "import secrets; print(secrets.token_hex(32))" | gopass insert development/jjohnson-47/flask-secret-key

# Update .env
echo "FLASK_SECRET_KEY=$(gopass show -o development/jjohnson-47/flask-secret-key)" >> .env
```

##### B. Course Platform Credentials

```bash
# Store course enrollment keys in gopass
gopass insert development/jjohnson-47/myopenmath/course-id
gopass insert development/jjohnson-47/myopenmath/enrollment-key
gopass insert development/jjohnson-47/edfinity/registration-code
```

#### 2. Create .env.secrets Template

```bash
# .env.secrets (for sensitive values only)
FLASK_SECRET_KEY=${FLASK_SECRET_KEY}
MYOPENMATH_COURSE_ID=${MYOPENMATH_COURSE_ID}
MYOPENMATH_ENROLLMENT_KEY=${MYOPENMATH_ENROLLMENT_KEY}
EDFINITY_REGISTRATION_CODE=${EDFINITY_REGISTRATION_CODE}
```

#### 3. Setup Script for Secret Loading

Create `scripts/load_secrets.sh`:

```bash
#!/bin/bash
# Load secrets from gopass into environment

export FLASK_SECRET_KEY=$(gopass show -o development/jjohnson-47/flask-secret-key)
export MYOPENMATH_COURSE_ID=$(gopass show -o development/jjohnson-47/myopenmath/course-id)
export MYOPENMATH_ENROLLMENT_KEY=$(gopass show -o development/jjohnson-47/myopenmath/enrollment-key)
export EDFINITY_REGISTRATION_CODE=$(gopass show -o development/jjohnson-47/edfinity/registration-code)
```

#### 4. Potential Future Secrets

Based on the codebase, you might need:

- **Blackboard API credentials** (if automating course management)
- **Email service credentials** (for notifications)
- **Database credentials** (if adding persistence)
- **Cloud storage keys** (for file backups)
- **LMS API tokens** (for grade sync)

### Gopass Organization Structure

Recommended hierarchy for this project:

```
development/
└── jjohnson-47/
    ├── flask-secret-key
    ├── github-token
    ├── myopenmath/
    │   ├── course-id
    │   └── enrollment-key
    ├── edfinity/
    │   └── registration-code
    ├── blackboard/
    │   ├── api-key
    │   └── api-secret
    └── email/
        ├── smtp-host
        ├── smtp-user
        └── smtp-pass
```

### Implementation Priority

1. **HIGH**: Flask SECRET_KEY (security vulnerability)
2. **MEDIUM**: Course enrollment keys (currently exposed)
3. **LOW**: Future API integrations (not yet needed)

### Multi-Machine Development Setup

#### Development Environments

- **Primary**: Fedora 42 (native Linux)
- **Secondary**: Fedora 42 (WSL on Windows)
- **Requirement**: Portable secrets management across both machines

#### Portable Secrets Strategy

##### Option 1: Gopass Sync (Recommended)

Leverage your existing gopass GitHub backup for seamless sync:

```bash
# On new machine (WSL or other)
# 1. Install gopass and age
sudo dnf install gopass age

# 2. Clone your gopass store
git clone git@github.com:verlyn13/gopass-secrets.git ~/.local/share/gopass/stores/root

# 3. Import your age key (store this securely!)
# You'll need to transfer your age identity from primary machine
scp primary-machine:~/.config/age/keys.txt ~/.config/age/

# 4. Initialize gopass with existing store
gopass init --store root

# 5. Verify access
gopass ls
```

##### Option 2: Encrypted .env.secrets File

For simpler setup without gopass on secondary machine:

```bash
# On primary machine
# 1. Create encrypted secrets file
age -e -i ~/.config/age/keys.txt -o .env.secrets.age .env.secrets

# 2. Commit encrypted file (safe to version control)
git add .env.secrets.age
git commit -m "Add encrypted secrets file"

# On secondary machine
# 1. Decrypt to .env.secrets (gitignored)
age -d -i ~/.config/age/keys.txt .env.secrets.age > .env.secrets

# 2. Source both env files
source .env && source .env.secrets
```

#### Development Setup Scripts

##### 1. Create `scripts/dev-setup.sh`

```bash
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
if command -v gopass &> /dev/null && gopass ls &> /dev/null; then
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
```

##### 2. Create `scripts/init-secrets.sh`

```bash
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
        echo "   On primary: cat ~/.config/age/keys.txt"
        echo "   Paste here (or manually create ~/.config/age/keys.txt)"
        read -p "Continue when ready..."

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
```

##### 3. Create `scripts/setup-gopass-secrets.sh`

```bash
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
```

##### 4. Create `scripts/load-secrets-gopass.sh`

```bash
#!/bin/bash
# Load secrets from gopass into environment

if ! command -v gopass &> /dev/null; then
    echo "❌ gopass not found"
    return 1
fi

# Flask secret
if gopass show development/jjohnson-47/flask-secret-key &> /dev/null; then
    export FLASK_SECRET_KEY=$(gopass show -o development/jjohnson-47/flask-secret-key)
fi

# Course platforms
if gopass show development/jjohnson-47/myopenmath/course-id &> /dev/null; then
    export MYOPENMATH_COURSE_ID=$(gopass show -o development/jjohnson-47/myopenmath/course-id)
    export MYOPENMATH_ENROLLMENT_KEY=$(gopass show -o development/jjohnson-47/myopenmath/enrollment-key)
fi

if gopass show development/jjohnson-47/edfinity/registration-code &> /dev/null; then
    export EDFINITY_REGISTRATION_CODE=$(gopass show -o development/jjohnson-47/edfinity/registration-code)
fi

echo "✅ Secrets loaded from gopass"
```

##### 5. Create `scripts/sync-secrets.sh`

```bash
#!/bin/bash
# Sync secrets between machines

echo "🔄 Syncing secrets configuration..."

# If using gopass
if command -v gopass &> /dev/null && [ -d ~/.local/share/gopass/stores/root/.git ]; then
    echo "Syncing gopass store..."
    cd ~/.local/share/gopass/stores/root
    git pull
    git push
    cd - > /dev/null
    echo "✅ Gopass synced"
fi

# If using encrypted file
if [ -f .env.secrets ] && command -v age &> /dev/null; then
    echo "Encrypting secrets for sync..."
    age -e -i ~/.config/age/keys.txt -o .env.secrets.age .env.secrets
    echo "✅ Encrypted .env.secrets.age ready for commit"
fi
```

#### Updated .gitignore

Add these entries:

```
# Secrets - never commit these
.env.secrets
.env.local
*.key
*.pem

# Encrypted secrets - safe to commit
.env.secrets.age

# Development
.env
```

#### Quick Start for New Machine

```bash
# 1. Clone the repository
git clone git@github.com:jjohnson-47/semester-2025-fall.git
cd semester-2025-fall

# 2. Run setup
./scripts/dev-setup.sh

# 3. Initialize secrets (first time only)
./scripts/init-secrets.sh

# 4. Activate and verify
source .venv/bin/activate
make validate
```

#### WSL-Specific Notes

1. **Age key transfer between machines**: Run `./scripts/transfer-age-key.sh` for guided options:
   - USB drive (most secure)
   - SSH transfer (if machines can connect)
   - Encrypted GitHub temporary file
   - QR code (for visual transfer)
   - Encrypted email

2. **Git SSH**: Ensure SSH keys are configured for GitHub:

   ```bash
   # Check SSH agent
   eval $(ssh-agent -s)
   ssh-add ~/.ssh/id_ed25519
   ```

3. **File permissions**: WSL may need permission fixes:

   ```bash
   # Fix script permissions
   chmod +x scripts/*.sh
   ```

### Next Steps

1. Generate and store Flask secret key in gopass
2. Move course credentials to gopass
3. Update code to read from environment variables
4. Create secret loading script
5. Test setup on WSL machine
6. Update documentation for secret management
7. Add pre-commit hooks to scan for secrets

Would you like me to help implement any of these recommendations?
