#!/bin/bash
# Verify multi-machine development setup

set -e

echo "🔍 Verifying Development Setup"
echo "==============================="
echo

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Track status
ALL_GOOD=true

# Check environment detection
echo "1. Environment Detection:"
if grep -q Microsoft /proc/version 2>/dev/null; then
    echo -e "   ${GREEN}✓${NC} WSL detected"
else
    echo -e "   ${GREEN}✓${NC} Native Linux detected"
fi
echo

# Check required tools
echo "2. Required Tools:"
for tool in python3 uv git; do
    if command -v $tool &> /dev/null; then
        echo -e "   ${GREEN}✓${NC} $tool installed"
    else
        echo -e "   ${RED}✗${NC} $tool missing"
        ALL_GOOD=false
    fi
done
echo

# Check optional tools
echo "3. Optional Tools:"
for tool in age gopass make; do
    if command -v $tool &> /dev/null; then
        echo -e "   ${GREEN}✓${NC} $tool installed"
    else
        echo -e "   ${YELLOW}⚠${NC} $tool not installed (optional)"
    fi
done
echo

# Check Python environment
echo "4. Python Environment:"
if [ -d ".venv" ]; then
    echo -e "   ${GREEN}✓${NC} Virtual environment exists"

    # Check Python version
    PYTHON_VERSION=$(.venv/bin/python --version 2>&1 | cut -d' ' -f2)
    echo -e "   ${GREEN}✓${NC} Python version: $PYTHON_VERSION"
else
    echo -e "   ${RED}✗${NC} Virtual environment missing"
    ALL_GOOD=false
fi
echo

# Check environment files
echo "5. Configuration Files:"
if [ -f ".env" ]; then
    echo -e "   ${GREEN}✓${NC} .env file exists"
else
    echo -e "   ${YELLOW}⚠${NC} .env file missing (will be created from template)"
fi

if [ -f ".env.secrets" ]; then
    echo -e "   ${GREEN}✓${NC} .env.secrets file exists"
elif [ -f ".env.secrets.age" ]; then
    echo -e "   ${GREEN}✓${NC} .env.secrets.age file exists (encrypted)"
elif command -v gopass &> /dev/null && gopass show development/jjohnson-47/flask-secret-key &> /dev/null 2>&1; then
    echo -e "   ${GREEN}✓${NC} Secrets in gopass"
else
    echo -e "   ${YELLOW}⚠${NC} No secrets configured (run ./scripts/init-secrets.sh)"
fi
echo

# Check age key (if age is installed)
echo "6. Age Encryption:"
if command -v age &> /dev/null; then
    if [ -f ~/.config/age/keys.txt ]; then
        echo -e "   ${GREEN}✓${NC} Age key exists"

        # Check permissions
        PERMS=$(stat -c %a ~/.config/age/keys.txt)
        if [ "$PERMS" = "600" ]; then
            echo -e "   ${GREEN}✓${NC} Age key permissions correct (600)"
        else
            echo -e "   ${YELLOW}⚠${NC} Age key permissions: $PERMS (should be 600)"
        fi
    else
        echo -e "   ${YELLOW}⚠${NC} Age key not found (needed for encrypted secrets)"
    fi
else
    echo -e "   ${YELLOW}⚠${NC} Age not installed"
fi
echo

# Check directories
echo "7. Project Directories:"
for dir in build dashboard/state content/courses; do
    if [ -d "$dir" ]; then
        echo -e "   ${GREEN}✓${NC} $dir exists"
    else
        echo -e "   ${YELLOW}⚠${NC} $dir missing (will be created)"
    fi
done
echo

# Check Git configuration
echo "8. Git Configuration:"
GIT_AUTOCRLF=$(git config --get core.autocrlf)
if [ "$GIT_AUTOCRLF" = "input" ] || [ "$GIT_AUTOCRLF" = "false" ]; then
    echo -e "   ${GREEN}✓${NC} Line endings configured correctly"
else
    echo -e "   ${YELLOW}⚠${NC} Line endings: $GIT_AUTOCRLF (should be 'input' or 'false')"
fi
echo

# Test Flask app configuration
echo "9. Flask Configuration:"
if [ -d ".venv" ]; then
    # Activate venv and test config
    source .venv/bin/activate

    # Test secret key
    FLASK_TEST=$(python -c "
from dashboard.config import Config
c = Config()
if len(c.SECRET_KEY) > 20 and c.SECRET_KEY != 'dev-key-change-in-production':
    print('secure')
else:
    print('insecure')
" 2>/dev/null) || FLASK_TEST="error"

    if [ "$FLASK_TEST" = "secure" ]; then
        echo -e "   ${GREEN}✓${NC} Flask secret key configured"
    elif [ "$FLASK_TEST" = "insecure" ]; then
        echo -e "   ${YELLOW}⚠${NC} Flask using default secret key"
    else
        echo -e "   ${RED}✗${NC} Error testing Flask configuration"
        ALL_GOOD=false
    fi
fi
echo

# Check script permissions
echo "10. Script Permissions:"
SCRIPTS_OK=true
for script in scripts/*.sh; do
    if [ -f "$script" ]; then
        if [ -x "$script" ]; then
            # Silent check, only report issues
            :
        else
            echo -e "   ${YELLOW}⚠${NC} $script not executable"
            SCRIPTS_OK=false
        fi
    fi
done
if [ "$SCRIPTS_OK" = "true" ]; then
    echo -e "   ${GREEN}✓${NC} All scripts executable"
fi
echo

# Summary
echo "================================"
if [ "$ALL_GOOD" = "true" ]; then
    echo -e "${GREEN}✅ Setup verified successfully!${NC}"
    echo
    echo "Next steps:"
    echo "1. Activate environment: source .venv/bin/activate"
    echo "2. Run validation: make validate"
    echo "3. Start dashboard: make dash"
else
    echo -e "${YELLOW}⚠️ Setup has some issues${NC}"
    echo
    echo "To complete setup:"
    echo "1. Run: ./scripts/dev-setup.sh"
    echo "2. Configure secrets: ./scripts/init-secrets.sh"
    echo "3. Then run this verification again"
fi
echo

# WSL-specific notes
if grep -q Microsoft /proc/version 2>/dev/null; then
    echo "📝 WSL-Specific Notes:"
    echo "- Use DASH_HOST=0.0.0.0 for Windows browser access"
    echo "- Check Windows Defender if ports are blocked"
    echo "- Use ./scripts/transfer-age-key.sh to transfer keys"
fi
