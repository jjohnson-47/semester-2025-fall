# Cloudflare Pages Management with `cf-go`

This system has `cf-go` installed. Use it to manage Cloudflare Pages for this project via the Cloudflare API with consistent, scriptable commands and CI-friendly exit codes.

## Prerequisites

- Environment: `CLOUDFLARE_API_TOKEN` (scoped), `CLOUDFLARE_ACCOUNT_ID`.
- Token scopes: include Account → Pages — Read/Edit (plus any other resources you use).
- Optional: store token in gopass at `cloudflare/tokens/projects/semester-2025-fall/pages`.

## Common Tasks

- List all Pages projects

  ```bash
  cf-go api GET accounts/$CLOUDFLARE_ACCOUNT_ID/pages/projects
  ```

- Inspect a project

  ```bash
  PROJECT=<name>
  cf-go api GET accounts/$CLOUDFLARE_ACCOUNT_ID/pages/projects/$PROJECT
  ```

- List recent deployments

  ```bash
  cf-go api GET accounts/$CLOUDFLARE_ACCOUNT_ID/pages/projects/$PROJECT/deployments
  ```

- Trigger a deployment from a branch (adjust as needed)

  ```bash
  BRANCH=main
  cf-go api POST accounts/$CLOUDFLARE_ACCOUNT_ID/pages/projects/$PROJECT/deployments \
    --data '{"deployment_trigger":{"metadata":{"branch":"'"$BRANCH"'"}},"env_vars":{}}'
  ```

## Makefile Helpers (optional)

```make
# List Pages projects
pages-list:
 cf-go api GET accounts/$(CLOUDFLARE_ACCOUNT_ID)/pages/projects

# Show one project: make pages-project PROJECT=<name>
pages-project:
 @test -n "$(PROJECT)" || (echo "PROJECT required" && exit 1)
 cf-go api GET accounts/$(CLOUDFLARE_ACCOUNT_ID)/pages/projects/$(PROJECT)

# List deployments: make pages-deployments PROJECT=<name>
pages-deployments:
 @test -n "$(PROJECT)" || (echo "PROJECT required" && exit 1)
 cf-go api GET accounts/$(CLOUDFLARE_ACCOUNT_ID)/pages/projects/$(PROJECT)/deployments

# Trigger deploy: make pages-deploy PROJECT=<name> BRANCH=main
pages-deploy:
 @test -n "$(PROJECT)" || (echo "PROJECT required" && exit 1)
 @test -n "$(BRANCH)" || (echo "BRANCH required" && exit 1)
 cf-go api POST accounts/$(CLOUDFLARE_ACCOUNT_ID)/pages/projects/$(PROJECT)/deployments \
   --data '{"deployment_trigger":{"metadata":{"branch":"'"$(BRANCH)"'"}},"env_vars":{}}'
```

## CI Tips

- Use `cf-go` for Pages reads/writes in workflows; keep `wrangler pages deploy` for static site uploads when applicable.
- Prefer project-scoped tokens in CI; avoid IP restrictions for hosted runners.
- `cf-go` exits with non-zero on API errors and prints actionable messages for debugging.
