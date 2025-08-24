#!/usr/bin/env bash
# Cloudflare Pages setup using cf-go
# Programmatically creates Pages project, configures domain, and sets up DNS

set -euo pipefail

# Colors for output
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Load project context
if [ ! -f ".cloudflare" ]; then
    echo -e "${RED}Error: .cloudflare file not found${NC}"
    echo "Please ensure you're in the project root directory"
    exit 1
fi

source .cloudflare

echo -e "${BLUE}════════════════════════════════════════════════${NC}"
echo -e "${BLUE}     Cloudflare Pages Setup with cf-go         ${NC}"
echo -e "${BLUE}════════════════════════════════════════════════${NC}"
echo ""
echo "Project: ${PAGES_PROJECT}"
echo "Zone: ${ZONE}"
echo "Custom Domain: ${PAGES_CUSTOM_DOMAIN}"
echo "Production Branch: ${PRODUCTION_BRANCH}"
echo ""

# Check for cf-go
if ! command -v cf-go &> /dev/null; then
    echo -e "${RED}Error: cf-go is not installed${NC}"
    echo "Install with: go install github.com/cloudflare/cf-go/cmd/cf-go@latest"
    exit 1
fi

# Check for jq
if ! command -v jq &> /dev/null; then
    echo -e "${YELLOW}Warning: jq is not installed (output will be raw JSON)${NC}"
    JQ_CMD="cat"
else
    JQ_CMD="jq"
fi

# Load credentials from gopass
echo -e "${BLUE}Loading credentials from gopass...${NC}"
export CLOUDFLARE_API_TOKEN=$(gopass show -o "${TOKEN_PATH}" 2>/dev/null) || {
    echo -e "${RED}Failed to load token from gopass${NC}"
    echo "Run: ./scripts/setup-cloudflare-token.sh first"
    exit 1
}

export CLOUDFLARE_ACCOUNT_ID=$(gopass show -o "${ACCOUNT_PATH}" 2>/dev/null) || {
    echo -e "${RED}Failed to load account ID from gopass${NC}"
    echo "Store with: gopass insert ${ACCOUNT_PATH}"
    exit 1
}

echo -e "${GREEN}✓ Credentials loaded${NC}"
echo ""

# Step 1: Check if project exists
echo -e "${BLUE}Step 1: Checking if Pages project exists...${NC}"
if cf-go api GET "accounts/${CLOUDFLARE_ACCOUNT_ID}/pages/projects/${PAGES_PROJECT}" 2>/dev/null | grep -q '"success":true'; then
    echo -e "${YELLOW}Project '${PAGES_PROJECT}' already exists${NC}"
    PROJECT_EXISTS=true
else
    echo "Project does not exist"
    PROJECT_EXISTS=false
fi
echo ""

# Step 2: Create project if needed
if [ "${PROJECT_EXISTS}" = false ]; then
    echo -e "${BLUE}Step 2: Creating Pages project...${NC}"
    RESPONSE=$(cf-go api POST "accounts/${CLOUDFLARE_ACCOUNT_ID}/pages/projects" \
        --data '{
            "name": "'"${PAGES_PROJECT}"'",
            "production_branch": "'"${PRODUCTION_BRANCH}"'",
            "build_config": {
                "build_command": "make build-site ENV=prod",
                "destination_dir": "site"
            }
        }' 2>&1)

    if echo "$RESPONSE" | grep -q '"success":true'; then
        echo -e "${GREEN}✓ Pages project '${PAGES_PROJECT}' created${NC}"
        SUBDOMAIN=$(echo "$RESPONSE" | jq -r '.result.subdomain' 2>/dev/null || echo "Check dashboard")
        echo "Pages URL: https://${SUBDOMAIN}.pages.dev"
    else
        echo -e "${RED}Failed to create project${NC}"
        echo "$RESPONSE" | $JQ_CMD
        exit 1
    fi
else
    echo -e "${BLUE}Step 2: Getting project details...${NC}"
    RESPONSE=$(cf-go api GET "accounts/${CLOUDFLARE_ACCOUNT_ID}/pages/projects/${PAGES_PROJECT}")
    SUBDOMAIN=$(echo "$RESPONSE" | jq -r '.result.subdomain' 2>/dev/null || echo "${PAGES_PROJECT}")
    echo "Pages URL: https://${SUBDOMAIN}.pages.dev"
fi
echo ""

# Step 3: Check domain attachment
echo -e "${BLUE}Step 3: Checking custom domain...${NC}"
DOMAINS=$(cf-go api GET "accounts/${CLOUDFLARE_ACCOUNT_ID}/pages/projects/${PAGES_PROJECT}" | \
    jq -r '.result.domains[]' 2>/dev/null || echo "")

if echo "$DOMAINS" | grep -q "${PAGES_CUSTOM_DOMAIN}"; then
    echo -e "${YELLOW}Domain '${PAGES_CUSTOM_DOMAIN}' already attached${NC}"
    DOMAIN_ATTACHED=true
else
    echo "Domain not attached"
    DOMAIN_ATTACHED=false
fi
echo ""

# Step 4: Attach domain if needed
if [ "${DOMAIN_ATTACHED}" = false ]; then
    echo -e "${BLUE}Step 4: Attaching custom domain...${NC}"
    RESPONSE=$(cf-go api POST "accounts/${CLOUDFLARE_ACCOUNT_ID}/pages/projects/${PAGES_PROJECT}/domains" \
        --data '{"name": "'"${PAGES_CUSTOM_DOMAIN}"'"}' 2>&1)

    if echo "$RESPONSE" | grep -q '"success":true'; then
        echo -e "${GREEN}✓ Domain '${PAGES_CUSTOM_DOMAIN}' attached${NC}"
    else
        echo -e "${YELLOW}Domain attachment may have failed (might already exist)${NC}"
        echo "$RESPONSE" | grep -o '"message":"[^"]*"' || true
    fi
else
    echo -e "${BLUE}Step 4: Domain already configured${NC}"
fi
echo ""

# Step 5: Configure DNS
echo -e "${BLUE}Step 5: Checking DNS configuration...${NC}"

# Check if CNAME exists
DNS_RECORDS=$(cf-go dns list "${ZONE}" 2>/dev/null || echo "")
if echo "$DNS_RECORDS" | grep -q "${PAGES_SUBDOMAIN}.*CNAME.*${SUBDOMAIN}.pages.dev"; then
    echo -e "${YELLOW}CNAME record already exists${NC}"
else
    echo "Creating CNAME record..."
    if cf-go dns add CNAME "${PAGES_SUBDOMAIN}" "${SUBDOMAIN}.pages.dev" --zone "${ZONE}"; then
        echo -e "${GREEN}✓ CNAME record created${NC}"
    else
        echo -e "${YELLOW}CNAME creation may have failed (might already exist)${NC}"
    fi
fi
echo ""

# Step 6: Verify nameservers
echo -e "${BLUE}Step 6: Verifying DNS setup...${NC}"
echo "Nameservers for ${ZONE}:"
cf-go ns "${ZONE}" || echo "Unable to fetch nameservers"
echo ""

# Step 7: Build site
echo -e "${BLUE}Step 7: Building site...${NC}"
if make build-site ENV=preview; then
    echo -e "${GREEN}✓ Site built successfully${NC}"
else
    echo -e "${YELLOW}Site build failed - check errors above${NC}"
fi
echo ""

# Step 8: Deployment instructions
echo -e "${BLUE}Step 8: Deployment${NC}"
echo "════════════════════════════════════════════════"
echo ""
echo "Option 1: Deploy with wrangler (immediate):"
echo "  wrangler pages deploy site --project-name ${PAGES_PROJECT}"
echo ""
echo "Option 2: Deploy via GitHub Actions:"
echo "  1. Push to GitHub"
echo "  2. Go to Actions → 'Cloudflare Pages Deploy'"
echo "  3. Run workflow with environment selection"
echo ""
echo "Option 3: Deploy with cf-go (manual trigger):"
echo "  make pages-deploy PROJECT=${PAGES_PROJECT} BRANCH=main"
echo ""

# Summary
echo -e "${GREEN}════════════════════════════════════════════════${NC}"
echo -e "${GREEN}              Setup Complete!                   ${NC}"
echo -e "${GREEN}════════════════════════════════════════════════${NC}"
echo ""
echo "Project: ${PAGES_PROJECT}"
echo "Pages URL: https://${SUBDOMAIN}.pages.dev"
echo "Custom Domain: https://${PAGES_CUSTOM_DOMAIN}"
echo ""
echo "Next steps:"
echo "1. Configure GitHub secrets (see docs/CLOUDFLARE_DEPLOYMENT.md)"
echo "2. Deploy the site using one of the options above"
echo "3. Verify at https://${PAGES_CUSTOM_DOMAIN}"
