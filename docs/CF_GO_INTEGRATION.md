# cf-go Integration Documentation

## Overview

This project uses [cf-go](https://github.com/cloudflare/cf-go) for programmatic Cloudflare Pages management. cf-go provides low-level API access with clean exit codes and integrates with gopass for secure credential management.

## Project Context

The `.cloudflare` file defines project-specific settings:

```bash
PROJECT_NAME=semester-2025-fall
PAGES_PROJECT=jeffsthings-courses
ZONE=jeffsthings.com
PRODUCTION_BRANCH=main
TOKEN_PATH=cloudflare/tokens/projects/semester-2025-fall/pages
ACCOUNT_PATH=cloudflare/account/id
PAGES_SUBDOMAIN=courses
PAGES_CUSTOM_DOMAIN=courses.jeffsthings.com
```

## cf-go Capabilities Used

### 1. Low-level API Access

- Direct API calls to any Cloudflare endpoint
- Pages, DNS, Zones management
- Clean exit codes for scripting

### 2. Project Context

- `.cloudflare` file for project settings
- gopass integration for secure token storage
- Per-project token scoping

### 3. DNS/Zone Helpers

- `cf-go zone` - Zone management
- `cf-go ns` - Nameserver verification
- `cf-go dns` - DNS record management

### 4. Token Flows

- Scoped API tokens (Pages:Edit only)
- Secure storage in gopass
- Environment variable loading

## Common Operations

### Create Pages Project

```bash
cf-go api POST accounts/$CLOUDFLARE_ACCOUNT_ID/pages/projects \
  --data '{"name":"jeffsthings-courses","production_branch":"main"}'
```

### Attach Custom Domain

```bash
cf-go api POST accounts/$CLOUDFLARE_ACCOUNT_ID/pages/projects/jeffsthings-courses/domains \
  --data '{"name":"courses.jeffsthings.com"}'
```

### Trigger Deployment

```bash
cf-go api POST accounts/$CLOUDFLARE_ACCOUNT_ID/pages/projects/jeffsthings-courses/deployments \
  --data '{"deployment_trigger":{"metadata":{"branch":"main"}}}'
```

### DNS Configuration

```bash
# Add CNAME for subdomain
cf-go dns add CNAME courses jeffsthings-courses.pages.dev --zone jeffsthings.com

# Verify nameservers
cf-go ns jeffsthings.com

# List DNS records
cf-go dns list jeffsthings.com
```

## Automation Scripts

### Complete Setup

```bash
# Automated setup wizard
./scripts/setup-pages-cf-go.sh

# Or use Make
make pages-setup
```

### Token Management

```bash
# Store token in gopass
./scripts/setup-cloudflare-token.sh

# Verify token
make pages-verify-token
```

## Environment Setup

### Required Environment Variables

```bash
# Load from gopass
export CLOUDFLARE_API_TOKEN=$(gopass show -o cloudflare/tokens/projects/semester-2025-fall/pages)
export CLOUDFLARE_ACCOUNT_ID=$(gopass show -o cloudflare/account/id)

# Or use Make targets which handle this automatically
make pages-load-context
```

### GitHub Actions Integration

The workflow reads these from GitHub secrets:

- `CLOUDFLARE_API_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID`
- `CF_PROJECT` (repository variable)

## Troubleshooting

### Token Issues

```bash
# Check token permissions
cf-go api GET user/tokens/verify

# Verify Pages access
make pages-verify-token
```

### DNS Issues

```bash
# Check nameservers
cf-go ns jeffsthings.com

# Verify DNS propagation
dig courses.jeffsthings.com

# List all DNS records
make dns-list
```

### Project Issues

```bash
# Check project status
make pages-status

# List deployments
make pages-deployments PROJECT=jeffsthings-courses

# View project details
cf-go api GET accounts/$CLOUDFLARE_ACCOUNT_ID/pages/projects/jeffsthings-courses
```

## API Endpoints Reference

### Pages

- List projects: `GET accounts/{account_id}/pages/projects`
- Create project: `POST accounts/{account_id}/pages/projects`
- Get project: `GET accounts/{account_id}/pages/projects/{project_name}`
- Attach domain: `POST accounts/{account_id}/pages/projects/{project_name}/domains`
- List deployments: `GET accounts/{account_id}/pages/projects/{project_name}/deployments`
- Trigger deployment: `POST accounts/{account_id}/pages/projects/{project_name}/deployments`

### DNS

- List records: `GET zones/{zone_id}/dns_records`
- Create record: `POST zones/{zone_id}/dns_records`
- Update record: `PUT zones/{zone_id}/dns_records/{record_id}`
- Delete record: `DELETE zones/{zone_id}/dns_records/{record_id}`

## Security Notes

1. **Token Scope**: Limited to Pages:Edit permission only
2. **Storage**: Tokens stored encrypted in gopass
3. **Access**: Project-specific token paths
4. **Rotation**: Regular token rotation recommended
5. **Audit**: All API calls logged by Cloudflare

## Advanced Usage

### Programmatic Deployment

```bash
# Build site
make build-site ENV=prod

# Deploy with cf-go
cf-go api POST accounts/$CLOUDFLARE_ACCOUNT_ID/pages/projects/jeffsthings-courses/deployments \
  --data '{"deployment_trigger":{"metadata":{"branch":"main"}}}'
```

### Custom Domain with Apex

For apex domain (jeffsthings.com):

1. Use CNAME flattening to `jeffsthings-courses.pages.dev`
2. Or attach via Pages API and let Cloudflare configure
3. Verify with `cf-go ns` and Pages domain status

### Environment-specific Deployments

```bash
# Preview environment
cf-go api POST ... --data '{"deployment_trigger":{"metadata":{"branch":"preview"}}}'

# Production
cf-go api POST ... --data '{"deployment_trigger":{"metadata":{"branch":"main"}}}'
```

## Next Steps

1. Install cf-go: `go install github.com/cloudflare/cf-go/cmd/cf-go@latest`
2. Configure token: `./scripts/setup-cloudflare-token.sh`
3. Run setup: `make pages-setup`
4. Deploy: `make pages-deploy PROJECT=jeffsthings-courses BRANCH=main`
