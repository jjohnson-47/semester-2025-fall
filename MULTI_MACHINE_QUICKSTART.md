# Multi-Machine Development Quick Reference

## 🚀 Quick Start (New Machine)

```bash
# 1. Clone and setup
git clone git@github.com:jjohnson-47/semester-2025-fall.git
cd semester-2025-fall
./scripts/dev-setup.sh

# 2. Configure secrets (choose one):
./scripts/init-secrets.sh  # Interactive setup

# 3. Activate and verify
source .venv/bin/activate
./scripts/verify-setup.sh
make validate
```

## 🔑 Secret Management Options

### Option 1: Gopass (Recommended for multi-machine)

```bash
# Primary machine
gopass insert development/jjohnson-47/flask-secret-key
./scripts/sync-secrets.sh

# Secondary machine
# Setup gopass, then:
./scripts/sync-secrets.sh
```

### Option 2: Age Encryption (Simple file-based)

```bash
# Primary machine
./scripts/init-secrets.sh  # Choose option 2
git add .env.secrets.age && git commit && git push

# Secondary machine
./scripts/transfer-age-key.sh  # Transfer key first
git pull
age -d -i ~/.config/age/keys.txt .env.secrets.age > .env.secrets
```

### Option 3: Manual (Quick testing)

```bash
cp .env.example .env
./scripts/create-secrets-interactive.sh
```

## 🔄 Age Key Transfer Methods

```bash
./scripts/transfer-age-key.sh
# Choose from:
# 1) USB drive (most secure)
# 2) SSH transfer (direct)
# 3) Encrypted GitHub (convenient)
# 4) QR code (visual)
# 5) Encrypted email
```

## 🪟 WSL-Specific Commands

```bash
# Fix permissions
find scripts -type f -name "*.sh" -exec chmod +x {} \;

# Dashboard access from Windows
DASH_HOST=0.0.0.0 make dash
# Browse to: http://localhost:5055

# Git line endings
git config core.autocrlf input
```

## ✅ Verification

```bash
# Full verification
./scripts/verify-setup.sh

# Quick checks
python --version           # Should be 3.13.6+
uv --version               # Package manager
echo $FLASK_SECRET_KEY     # Should show if configured
make validate              # Run all checks
```

## 📁 Important Files

```
.env                 # Base configuration (gitignored)
.env.secrets         # Sensitive values (NEVER commit)
.env.secrets.age     # Encrypted secrets (safe to commit)
~/.config/age/keys.txt     # Age identity key (BACKUP THIS!)
```

## 🛠️ Common Commands

```bash
# Development
make dash            # Start dashboard
make test            # Run tests
make validate        # Full validation
make syllabi         # Generate syllabi
make reprioritize    # Update task priorities

# Secrets
./scripts/sync-secrets.sh        # Sync between machines
./scripts/init-secrets.sh        # Initial setup
./scripts/verify-setup.sh        # Verify everything

# Git workflow
ds status            # Check all repos (if using ds CLI)
git status           # Check this repo
```

## 🚨 Troubleshooting

### "Permission denied" on scripts

```bash
chmod +x scripts/*.sh
```

### "age: no identity matched"

```bash
# Check key exists
ls -la ~/.config/age/keys.txt
# Transfer from primary machine
./scripts/transfer-age-key.sh
```

### WSL: Port already in use

```bash
lsof -i :5055
kill -9 <PID>
# Or use different port
DASH_PORT=5056 make dash
```

### Secrets not loading

```bash
# Check which method is configured
./scripts/verify-setup.sh
# Reinitialize if needed
./scripts/init-secrets.sh
```

## 📝 Notes

- The setup is idempotent - safe to re-run anytime
- Secrets are loaded in order: .env → .env.secrets → environment variables
- WSL requires `DASH_HOST=0.0.0.0` for Windows browser access
- All scripts in `scripts/` should be executable
- Keep age keys backed up securely!
