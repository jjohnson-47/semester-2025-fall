# Cloudflare Pages Deployment (Historical Reference)

> **Retired on 2026-07-14.** This document records the publication surface
> used during the Fall 2025 semester. It is not an active deployment runbook.
> The existing Pages site is retained as a public archive; repository changes
> do not publish automatically. See
> [`adr/0005-retained-public-archive.md`](adr/0005-retained-public-archive.md).

## Current Archive Boundary

The repository continues to preserve:

- the V2 source and local site builder;
- the checked-in `site/` archive output and Cloudflare configuration;
- the public archive at <https://courses.jeffsthings.com/>; and
- read-only project and deployment inspection targets.

The following Fall 2025 operations are retired:

- pull-request and `main`-branch Pages deployment;
- manual or dashboard-triggered publication;
- credential creation, rotation, retrieval, or installation for this project;
- Pages project, domain, or DNS mutation; and
- recurring semester maintenance.

Do not run the historical token-setup scripts, recreate GitHub deployment
secrets, or invoke Cloudflare mutation targets merely to publish repository
changes. The Makefile fails closed on mutation targets unless a new owner
decision is accompanied by `ARCHIVE_REACTIVATION_APPROVED=1`.

## Supported Local Archive Build

Local generation remains current and does not mutate Cloudflare:

```bash
BUILD_MODE=v2 make validate
BUILD_MODE=v2 make build-site ENV=preview
test -f site/manifest.json
test -f site/_headers
```

For a local browser preview, use the repository's local serving target after a
successful build:

```bash
BUILD_MODE=v2 make serve-site
```

A successful local build demonstrates reproducibility only. It is not evidence
that a new version was deployed.

## Read-Only Archive Inspection

When already-authorized local credentials exist, these targets inspect the
retained Pages resource without changing it:

```bash
make pages-status PROJECT=jeffsthings-courses
make pages-project PROJECT=jeffsthings-courses
make pages-deployments PROJECT=jeffsthings-courses
```

Public behavior can also be checked without Cloudflare credentials:

```bash
curl -fsSI https://courses.jeffsthings.com/
curl -fsS https://courses.jeffsthings.com/manifest.json | jq .
```

These observations describe the live retained resource. They do not authorize
changes to it.

## Historical Fall 2025 Design

During active teaching, the repository was designed around a Cloudflare Pages
project named `jeffsthings-courses`, with the custom public domain above and a
Pages fallback domain. The former runbook supported direct uploads, GitHub
Actions triggers, a dashboard deployment control, and a narrowly scoped
Pages-edit token stored outside the repository. It also described gradual
publication phases for the manifest, syllabi, and schedules.

Those details are preserved here to explain the checked-in configuration and
historical reports. They are not current operating instructions. In particular:

- no Cloudflare API token is required for local validation or site generation;
- no GitHub Actions deployment secrets should be added or refreshed;
- pushes and pull requests no longer trigger Pages publication; and
- the old dashboard deployment API has been removed.

## Reactivation Gate

Publication may be restored only after the repository owner explicitly reopens
it and all requirements in ADR 0005 are satisfied. A reactivation review must
confirm the intended Cloudflare account, Pages project, production branch,
domain behavior, off-repository credential custody, safe workflow triggers, and
a clean-checkout build before any external mutation occurs.
