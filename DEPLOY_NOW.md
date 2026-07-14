# Publication Is Retired

As of 2026-07-14, this repository is a retained public archive. The published
Fall 2025 course site remains available, but automatic Pages deployment,
scheduled maintenance, and dashboard deployment controls are retired.

Do not create, rotate, retrieve, or install Cloudflare credentials merely to
publish repository changes. A push to `main` no longer deploys the site.

## Safe Archive Verification

```bash
BUILD_MODE=v2 make validate
BUILD_MODE=v2 make build-site ENV=preview
test -f site/manifest.json
test -f site/_headers
```

These commands rebuild and validate local output only. They do not mutate
Cloudflare or DNS.

## Reactivation Requires a New Decision

Publication may be restored only after the owner explicitly reopens it and the
requirements in
[`docs/adr/0005-retained-public-archive.md`](docs/adr/0005-retained-public-archive.md)
are satisfied. Repository Cloudflare mutation targets additionally require the
one-shot environment flag `ARCHIVE_REACTIVATION_APPROVED=1`.
