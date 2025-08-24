# Quick Cloudflare Token Setup

## Step 1: Run the Setup Script

```bash
./scripts/setup-cloudflare-token.sh
```

## Step 2: When Prompted, Create Token in Cloudflare

1. Go to: <https://dash.cloudflare.com/profile/api-tokens>
2. Click "Create Token" → "Custom token"
3. Configure with:
   - **Token name**: `semester-2025-fall-pages`
   - **Permissions**: Account → Cloudflare Pages → Edit
   - **Account Resources**: Include → Your Account (13eb584192d9cefb730fde0cfd271328)
   - **IP Filtering**: Leave empty
   - **TTL**: Leave empty
4. Click "Continue to summary" → "Create Token"
5. **COPY THE TOKEN** (you only see it once!)

## Step 3: Paste Token in Terminal

When the script prompts "Paste the token below", paste it and press Enter.

## Step 4: Verify It Worked

```bash
# Check token is stored
gopass show cloudflare/tokens/projects/semester-2025-fall/pages

# Verify with cf-go (if installed)
export CLOUDFLARE_API_TOKEN=$(gopass show -o cloudflare/tokens/projects/semester-2025-fall/pages)
export CLOUDFLARE_ACCOUNT_ID=$(gopass show -o cloudflare/account/id)
make pages-verify-token
```

## Alternative: Manual Storage

If the script has issues, store manually:

```bash
# Store token (paste when prompted)
gopass insert cloudflare/tokens/projects/semester-2025-fall/pages

# Store metadata
cat <<'EOF' | gopass insert -m cloudflare/tokens/projects/semester-2025-fall/pages/meta
name: semester-2025-fall-pages
account_id: 13eb584192d9cefb730fde0cfd271328
created: $(date -Iseconds)
permissions:
  - "Account: Cloudflare Pages — Edit"
EOF
```

## After Token is Stored

The token will be used for:

1. GitHub Actions deployments (add as secret)
2. cf-go operations (Make targets)
3. Programmatic Pages management

Run `make pages-setup` to create the Pages project once token is configured.
