# Cloudflare Pages Deployment Guide

## Prerequisites

1. **Cloudflare Account**: Active account with Pages access
2. **gopass**: Installed and configured for secret management
3. **cf-go**: For programmatic setup (`go install github.com/cloudflare/cf-go/cmd/cf-go@latest`)

## Setup Process

### Quick Setup with cf-go (Recommended)

```bash
# 1. Configure token and credentials
./scripts/setup-cloudflare-token.sh

# 2. Run complete Pages setup
./scripts/setup-pages-cf-go.sh

# 3. Or use the Make wizard
make pages-setup
```

### Manual Setup Steps

#### 1. Configure Cloudflare Token

Run the automated setup script:

```bash
./scripts/setup-cloudflare-token.sh
```

This script will:

- Store your Cloudflare Account ID in gopass
- Guide you through creating an API token
- Store the token securely in gopass
- Verify token access with cf-go

### 2. Manual Token Creation (Alternative)

If you prefer manual setup:

1. Go to [Cloudflare Dashboard → API Tokens](https://dash.cloudflare.com/profile/api-tokens)
2. Create a custom token with:
   - **Name**: `semester-2025-fall-pages`
   - **Permissions**: Account → Cloudflare Pages:Edit
   - **Resources**: Your account ID
   - **IP Filtering**: Leave empty (for CI/CD)

3. Store in gopass:

```bash
# Store token
gopass insert cloudflare/tokens/projects/semester-2025-fall/pages

# Store account ID
gopass insert cloudflare/account/id
```

### 3. Verify Token Access

```bash
# Export credentials
export CLOUDFLARE_ACCOUNT_ID=$(gopass show -o cloudflare/account/id)
export CLOUDFLARE_API_TOKEN=$(gopass show -o cloudflare/tokens/projects/semester-2025-fall/pages)

# Verify with Make
make pages-verify-token

# Or verify with cf-go directly
cf-go api GET accounts/$CLOUDFLARE_ACCOUNT_ID/pages/projects
```

### 4. Configure GitHub Repository

Add these secrets in GitHub (Settings → Secrets and variables → Actions):

| Type | Name | Value | How to Get |
|------|------|-------|------------|
| Secret | `CLOUDFLARE_API_TOKEN` | Your API token | `gopass show -o cloudflare/tokens/projects/semester-2025-fall/pages` |
| Secret | `CLOUDFLARE_ACCOUNT_ID` | Your account ID | `gopass show -o cloudflare/account/id` |
| Variable | `CF_PROJECT` | `jeffsthings-courses` | Fixed value |

### 5. Create Cloudflare Pages Project

1. Go to [Cloudflare Dashboard → Pages](https://dash.cloudflare.com/?to=/:account/pages)
2. Create a new project named `jeffsthings-courses`
3. Skip the GitHub integration (we use direct upload)
4. Note the project URL for verification

## Deployment Workflow

### Local Testing

```bash
# Build site locally
make build-site ENV=preview

# Verify structure
ls -la site/
cat site/manifest.json

# Test with local server
make serve-site
# Visit http://localhost:8000
```

### Manual Deployment (GitHub Actions)

1. Go to Actions → "Cloudflare Pages Deploy"
2. Click "Run workflow"
3. Select environment:
   - `preview` for testing
   - `prod` for production
4. Click "Run workflow"

### Automatic Deployment

- **Pull Requests**: Deploy to preview branch automatically
- **Main branch**: Deploy to production automatically (if configured)

## Deployment Phases

### Phase 0: Empty Structure (Current)

```bash
# Deploys only manifest and headers
make build-site ENV=preview
```

### Phase 1: Syllabus Only

```bash
# Include syllabus pages
$(PYTHON) scripts/site_build.py --include-docs syllabus
```

### Phase 2: Full Content

```bash
# Include both syllabus and schedule
$(PYTHON) scripts/site_build.py --include-docs syllabus schedule
```

## Verification Steps

### 1. Check Deployment Status

```bash
# List all deployments
make pages-deployments PROJECT=jeffsthings-courses

# Check project details
make pages-project PROJECT=jeffsthings-courses
```

### 2. Verify Security Headers

```bash
# Check CSP headers
curl -I https://jeffsthings-courses.pages.dev | grep -i content-security

# Should see: frame-ancestors 'none'
```

### 3. Verify Manifest

```bash
curl https://jeffsthings-courses.pages.dev/manifest.json | jq .
```

## Troubleshooting

### Token Issues

```bash
# Re-verify token
make pages-verify-token

# Check token metadata
gopass show cloudflare/tokens/projects/semester-2025-fall/pages/meta
```

### Build Issues

```bash
# Clean and rebuild
make clean
make build-site ENV=preview

# Check for validation errors
make validate
```

### Deployment Failures

1. Check GitHub Actions logs
2. Verify secrets are set correctly
3. Ensure CF_PROJECT variable is set
4. Check Cloudflare Pages dashboard for errors

## Security Notes

- Token has minimal scope (Pages:Edit only)
- No IP restrictions for CI/CD compatibility
- CSP headers prevent iframe embedding
- Default excludes all content (explicit include required)

## Make Targets Reference

### Site Building

| Target | Description |
|--------|-------------|
| `make build-site` | Build public site (empty by default) |
| `make serve-site` | Local preview server |

### cf-go Pages Operations

| Target | Description |
|--------|-------------|
| `make pages-setup` | Complete setup wizard (create project, domain, DNS) |
| `make pages-env` | Show current Cloudflare environment |
| `make pages-create` | Create Pages project programmatically |
| `make pages-attach-domain` | Attach custom domain to project |
| `make pages-status` | Show project status and domains |
| `make pages-verify-token` | Verify API token |
| `make pages-list` | List all Pages projects |
| `make pages-project PROJECT=name` | Show project details |
| `make pages-deployments PROJECT=name` | List deployments |
| `make pages-deploy PROJECT=name BRANCH=main` | Trigger deployment |

### DNS Management

| Target | Description |
|--------|-------------|
| `make dns-list` | List all DNS records for zone |
| `make dns-add-cname` | Add CNAME for Pages subdomain |
| `make dns-verify` | Verify DNS and nameservers |

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `CLOUDFLARE_API_TOKEN` | Pages API token | Yes |
| `CLOUDFLARE_ACCOUNT_ID` | Account identifier | Yes |
| `CF_PROJECT` | Pages project name | Yes (in GitHub) |
| `ENV` | Environment (preview/prod) | No (default: preview) |
| `ACADEMIC_TERM` | Term for URLs | No (default: fall-2025) |

## Next Steps

1. Run `./scripts/setup-cloudflare-token.sh`
2. Configure GitHub secrets
3. Create Pages project in Cloudflare
4. Trigger first deployment (empty structure)
5. Verify headers and manifest
6. Gradually enable content as needed
