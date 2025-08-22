# Multi-Machine Development Setup Guide

## Overview

This guide ensures seamless development across multiple machines, specifically optimized for:

- **Primary**: Fedora 42 (native Linux)
- **Secondary**: Fedora 42 (WSL2 on Windows)
- **Future**: Any Unix-like environment with bash

## Quick Start (New Machine)

```bash
# 1. Clone repository
git clone git@github.com:jjohnson-47/semester-2025-fall.git
cd semester-2025-fall

# 2. Run universal setup
./scripts/dev-setup.sh

# 3. Initialize secrets (first time only)
./scripts/init-secrets.sh

# 4. Activate environment
source .venv/bin/activate

# 5. Verify setup
make validate
```

## Detailed Setup Instructions

### Prerequisites

#### Required Tools

- Git (with SSH configured for GitHub)
- Python 3.13.6+
- UV package manager

#### Optional (but recommended)

- age (for encryption)
- gopass (for secret management)
- make (for automation)

### Step 1: Environment Detection

The `dev-setup.sh` script automatically detects your environment:

```bash
# Detects WSL
if grep -q Microsoft /proc/version 2>/dev/null; then
    ENV_TYPE="wsl"
fi
```

WSL-specific adjustments applied:

- Git line ending configuration (`core.autocrlf input`)
- Script permission fixes
- Path normalization

### Step 2: Secrets Management

Three options available via `init-secrets.sh`:

#### Option 1: Gopass with GitHub Sync (Recommended)

**Setup on primary machine:**

```bash
# Store secrets in gopass
gopass insert development/jjohnson-47/flask-secret-key
gopass insert development/jjohnson-47/myopenmath/enrollment-key

# Sync to GitHub
cd ~/.local/share/gopass/stores/root
git push
```

**Setup on secondary machine:**

```bash
# Install gopass
sudo dnf install -y gopass age

# Clone your gopass store
git clone git@github.com:verlyn13/gopass-secrets.git \
    ~/.local/share/gopass/stores/root

# Transfer age key (see Age Key Transfer section)
# Then initialize
gopass init --store root
```

#### Option 2: Age-Encrypted File

**On primary machine:**

```bash
# Create and encrypt secrets
cat > .env.secrets << EOF
FLASK_SECRET_KEY=your-secret-here
MYOPENMATH_ENROLLMENT_KEY=math221fall2025
EOF

age -e -i ~/.config/age/keys.txt -o .env.secrets.age .env.secrets
git add .env.secrets.age
git commit -m "Add encrypted secrets"
git push
```

**On secondary machine:**

```bash
# Pull and decrypt
git pull
age -d -i ~/.config/age/keys.txt .env.secrets.age > .env.secrets
```

#### Option 3: Manual Configuration

Create `.env.secrets` manually:

```bash
cat > .env.secrets << 'EOF'
# Generate with: python -c "import secrets; print(secrets.token_hex(32))"
FLASK_SECRET_KEY=your-secret-key-here
MYOPENMATH_ENROLLMENT_KEY=math221fall2025
EDFINITY_REGISTRATION_CODE=H7C84FUR
EOF
```

### Step 3: Age Key Transfer

Use `./scripts/transfer-age-key.sh` for secure transfer between machines:

#### Method 1: USB Drive (Most Secure)

```bash
# On primary
./scripts/transfer-age-key.sh
# Choose option 1, follow prompts

# On secondary
# Insert USB, mount, copy key
```

#### Method 2: SSH Transfer (Direct)

```bash
# From secondary machine
scp primary-machine:~/.config/age/keys.txt ~/.config/age/
chmod 600 ~/.config/age/keys.txt
```

#### Method 3: Encrypted GitHub (Convenient)

```bash
# On primary
./scripts/transfer-age-key.sh
# Choose option 3, set passphrase

# On secondary
git pull
# Decrypt with passphrase when prompted
```

#### Method 4: QR Code (Visual)

```bash
# On primary
./scripts/transfer-age-key.sh
# Choose option 4

# On secondary
# Scan QR code, save to ~/.config/age/keys.txt
```

### Step 4: Python Environment

UV handles Python version and dependencies:

```bash
# Automatic in dev-setup.sh
uv venv
uv sync --all-extras --dev

# Manual activation
source .venv/bin/activate
```

### Step 5: Verification

Run these checks to ensure proper setup:

```bash
# Check Python
python --version  # Should be 3.13.6+

# Check UV
uv --version

# Check secrets loaded
echo $FLASK_SECRET_KEY  # Should show if secrets configured

# Run validation
make validate

# Test dashboard
make dash  # Access at http://localhost:5055
```

## WSL-Specific Configuration

### File Permissions

WSL may have permission issues with scripts:

```bash
# Fix all scripts
find scripts -type f -name "*.sh" -exec chmod +x {} \;

# Fix specific issues
chmod 600 ~/.config/age/keys.txt
chmod 700 ~/.config/age
```

### Network Access

For dashboard access from Windows host:

```bash
# In WSL, use 0.0.0.0 instead of 127.0.0.1
DASH_HOST=0.0.0.0 make dash

# From Windows browser
http://localhost:5055
```

### Git Configuration

WSL needs proper line ending handling:

```bash
# Set globally for WSL
git config --global core.autocrlf input
git config --global core.eol lf

# Project-specific (automatic in dev-setup.sh)
git config core.autocrlf input
```

### SSH Agent

Ensure SSH agent is running for GitHub:

```bash
# Add to ~/.bashrc
eval $(ssh-agent -s) > /dev/null 2>&1
ssh-add ~/.ssh/id_ed25519 2>/dev/null

# Or use keychain
sudo dnf install keychain
echo 'eval $(keychain --eval --quiet id_ed25519)' >> ~/.bashrc
```

## Environment Files Structure

```
.env                 # Non-sensitive configuration (tracked)
.env.example         # Template for .env (tracked)
.env.secrets         # Sensitive values (NEVER track)
.env.secrets.age     # Encrypted secrets (safe to track)
```

### Loading Order

1. `.env` - Base configuration
2. `.env.secrets` - Sensitive overrides
3. Environment variables - Runtime overrides

### Usage in Code

```python
# dashboard/config.py
import os
from pathlib import Path
from dotenv import load_dotenv

# Load base config
load_dotenv()

# Load secrets if available
secrets_file = Path('.env.secrets')
if secrets_file.exists():
    load_dotenv(secrets_file)

# Access with fallbacks
SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-key-change-in-production')
```

## Syncing Between Machines

### Using Gopass

```bash
# On any machine after changes
cd ~/.local/share/gopass/stores/root
git pull && git push

# Or use helper
./scripts/sync-secrets.sh
```

### Using Age-Encrypted Files

```bash
# After changing secrets
age -e -i ~/.config/age/keys.txt -o .env.secrets.age .env.secrets
git add .env.secrets.age
git commit -m "Update encrypted secrets"
git push

# On other machine
git pull
age -d -i ~/.config/age/keys.txt .env.secrets.age > .env.secrets
```

## Troubleshooting

### Common Issues

#### "Permission denied" on scripts

```bash
chmod +x scripts/*.sh
```

#### "command not found: uv"

```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc
```

#### "age: no identity matched"

```bash
# Check key exists
ls -la ~/.config/age/keys.txt

# Regenerate if needed
age-keygen -o ~/.config/age/keys.txt
```

#### "gopass: store not found"

```bash
# Reinitialize
gopass init --store root
```

#### WSL: "bind: address already in use"

```bash
# Find and kill process
lsof -i :5055
kill -9 <PID>

# Or use different port
DASH_PORT=5056 make dash
```

### Debug Mode

Enable verbose output for troubleshooting:

```bash
# Verbose setup
bash -x ./scripts/dev-setup.sh

# Debug secrets
GOPASS_DEBUG=true gopass show development/jjohnson-47/flask-secret-key

# Test environment
python -c "import os; print(os.environ.get('FLASK_SECRET_KEY', 'NOT SET'))"
```

## Security Best Practices

### Do's

- ✅ Use unique Flask secret keys per environment
- ✅ Rotate secrets regularly
- ✅ Use age encryption for file-based secrets
- ✅ Keep age keys backed up securely
- ✅ Use SSH keys for GitHub access

### Don'ts

- ❌ Never commit `.env.secrets` unencrypted
- ❌ Don't share age keys via unencrypted channels
- ❌ Avoid hardcoding secrets in code
- ❌ Don't use production secrets in development
- ❌ Never store secrets in Docker images

## Maintenance

### Regular Tasks

```bash
# Weekly: Sync secrets
./scripts/sync-secrets.sh

# Monthly: Update dependencies
uv sync --upgrade

# Per semester: Rotate secrets
python -c "import secrets; print(secrets.token_hex(32))" | \
    gopass insert -f development/jjohnson-47/flask-secret-key
```

### Backup Strategy

1. **Age keys**: Store encrypted copy in password manager
2. **Gopass store**: Automated GitHub backup
3. **Project data**: Regular git commits
4. **Generated files**: Not needed (regeneratable)

## Quick Reference

### Essential Commands

```bash
# Setup
./scripts/dev-setup.sh          # Full environment setup
./scripts/init-secrets.sh       # Secret initialization

# Development
source .venv/bin/activate       # Activate Python env
make dash                        # Start dashboard
make test                        # Run tests
make validate                    # Validate everything

# Secrets
./scripts/sync-secrets.sh       # Sync between machines
./scripts/transfer-age-key.sh   # Transfer age key

# Generation
make syllabi                     # Generate syllabi
make reprioritize               # Update task priorities
```

### File Locations

```
~/.config/age/keys.txt           # Age identity key
~/.local/share/gopass/stores/    # Gopass stores
.env.secrets                     # Local secrets (gitignored)
.env.secrets.age                 # Encrypted secrets
dashboard/state/                 # Task data
build/                          # Generated outputs
```

## Support

For issues specific to multi-machine setup:

1. Check this guide's Troubleshooting section
2. Review scripts in `scripts/` directory
3. Check environment with `./scripts/dev-setup.sh`
4. Verify secrets with `env | grep -E "(FLASK|MATH|EDFINITY)"`

Remember: The setup is designed to be idempotent - you can safely re-run `dev-setup.sh` anytime.
