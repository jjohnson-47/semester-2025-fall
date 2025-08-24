#!/usr/bin/env bash
# Setup Cloudflare Pages token for semester-2025-fall deployment
# Following cf-go recommendations for token management

set -euo pipefail

# Colors for output
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Project configuration
PROJECT_NAME="semester-2025-fall"
TOKEN_NAME="${PROJECT_NAME}-pages"
GOPASS_TOKEN_PATH="cloudflare/tokens/projects/${PROJECT_NAME}/pages"
GOPASS_META_PATH="cloudflare/tokens/projects/${PROJECT_NAME}/pages/meta"
GOPASS_ACCOUNT_PATH="cloudflare/account/id"

echo -e "${BLUE}Cloudflare Pages Token Setup for ${PROJECT_NAME}${NC}"
echo "=================================================="

# Step 1: Check for gopass
if ! command -v gopass &> /dev/null; then
    echo -e "${RED}Error: gopass is not installed${NC}"
    echo "Install gopass first: https://www.gopass.pw/"
    exit 1
fi

# Step 2: Check for cf-go
if ! command -v cf-go &> /dev/null; then
    echo -e "${YELLOW}Warning: cf-go is not installed${NC}"
    echo "Install cf-go for verification: go install github.com/cloudflare/cf-go/cmd/cf-go@latest"
    SKIP_VERIFY=true
else
    SKIP_VERIFY=false
fi

# Step 3: Resolve Account ID
echo -e "\n${BLUE}Step 1: Resolving Cloudflare Account ID${NC}"
if gopass show "${GOPASS_ACCOUNT_PATH}" &> /dev/null; then
    export CLOUDFLARE_ACCOUNT_ID=$(gopass show -o "${GOPASS_ACCOUNT_PATH}")
    echo -e "${GREEN}✓ Account ID found${NC}"
else
    echo -e "${YELLOW}Account ID not found in gopass${NC}"
    read -p "Enter your Cloudflare Account ID: " CLOUDFLARE_ACCOUNT_ID
    echo -e "Storing Account ID in gopass..."
    echo "${CLOUDFLARE_ACCOUNT_ID}" | gopass insert -f "${GOPASS_ACCOUNT_PATH}"
    export CLOUDFLARE_ACCOUNT_ID
fi

# Step 4: Display token creation instructions
echo -e "\n${BLUE}Step 2: Create API Token in Cloudflare Dashboard${NC}"
echo "1. Go to: https://dash.cloudflare.com/profile/api-tokens"
echo "2. Click 'Create Token' → 'Custom token'"
echo "3. Configure with these settings:"
echo "   - Token name: ${TOKEN_NAME}"
echo "   - Permissions: Account → Cloudflare Pages:Edit"
echo "   - Account Resources: Include → ${CLOUDFLARE_ACCOUNT_ID}"
echo "   - IP Filtering: Leave empty (for CI/CD)"
echo "   - TTL: Leave empty (no expiration)"
echo "4. Click 'Continue to summary' → 'Create Token'"
echo "5. Copy the token value"
echo ""
read -p "Press Enter when you have copied the token..."

# Step 5: Store token in gopass
echo -e "\n${BLUE}Step 3: Store Token in Gopass${NC}"
echo "Paste the token below (input will be hidden):"
gopass insert -f "${GOPASS_TOKEN_PATH}"

# Step 6: Store metadata
echo -e "\n${BLUE}Step 4: Store Token Metadata${NC}"
cat <<YAML | gopass insert -f -m "${GOPASS_META_PATH}"
name: ${TOKEN_NAME}
account_id: ${CLOUDFLARE_ACCOUNT_ID}
created: $(date -Iseconds)
permissions:
  - "Account: Cloudflare Pages — Edit"
resources:
  - account: ${CLOUDFLARE_ACCOUNT_ID}
allowed_ips: []
notes: |
  Permissive Pages token for CI/CD automation in ${PROJECT_NAME}.
  Used by GitHub Actions for Cloudflare Pages deployment.
YAML
echo -e "${GREEN}✓ Metadata stored${NC}"

# Step 7: Verify token (if cf-go available)
if [ "${SKIP_VERIFY}" = false ]; then
    echo -e "\n${BLUE}Step 5: Verify Token with cf-go${NC}"
    export CLOUDFLARE_API_TOKEN=$(gopass show -o "${GOPASS_TOKEN_PATH}")

    if cf-go api GET "accounts/${CLOUDFLARE_ACCOUNT_ID}/pages/projects" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Token verified successfully${NC}"
        echo "Token has proper Pages access"
    else
        echo -e "${RED}✗ Token verification failed${NC}"
        echo "Please check token permissions"
        exit 1
    fi
else
    echo -e "\n${YELLOW}Skipping verification (cf-go not installed)${NC}"
fi

# Step 8: GitHub configuration instructions
echo -e "\n${BLUE}Step 6: Configure GitHub Secrets${NC}"
echo "=================================================="
echo "Add these secrets to your GitHub repository:"
echo "(Settings → Secrets and variables → Actions)"
echo ""
echo "1. CLOUDFLARE_API_TOKEN:"
echo "   gopass show -o ${GOPASS_TOKEN_PATH}"
echo ""
echo "2. CLOUDFLARE_ACCOUNT_ID:"
echo "   gopass show -o ${GOPASS_ACCOUNT_PATH}"
echo ""
echo "3. Add repository variable CF_PROJECT:"
echo "   Value: jeffsthings-courses"
echo ""
echo -e "${GREEN}✓ Setup complete!${NC}"
echo ""
echo "Test deployment with:"
echo "  make build-site ENV=preview"
echo "  # Then trigger GitHub Actions workflow manually"

# Optional: Export for immediate use
echo -e "\n${BLUE}Environment variables exported for this session:${NC}"
echo "  CLOUDFLARE_API_TOKEN (hidden)"
echo "  CLOUDFLARE_ACCOUNT_ID=${CLOUDFLARE_ACCOUNT_ID}"
