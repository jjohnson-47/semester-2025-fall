# ADR 0005: Retained Public Archive

- Status: Accepted
- Date: 2026-07-14
- Decision owner: repository owner

## Context

The Fall 2025 teaching term ended on December 13, 2025. The published course
site remains useful as evidence of completed teaching, but its deployment token
is no longer valid and the repository still contained automation and tests for
semester-local resources that were never portable to a clean checkout.

Those historical surfaces included:

- automatic Cloudflare Pages deployment on pull requests and main pushes;
- a scheduled maintenance workflow whose future-date checks cannot apply to a
  completed semester;
- an unregistered dashboard deployment blueprint targeting an absent sibling
  checkout; and
- an orchestration-completion test requiring ignored SQLite and tracker state.

The 2026-07-14 GitHub audit confirmed that these were retirement candidates,
not healthy current services:

- `Cloudflare Pages Deploy` was still active and its run for the manifest merge
  failed with Cloudflare authentication error 10000; and
- `Scheduled Maintenance` was already `disabled_inactivity`, after repeated
  failed scheduled runs ending on 2025-12-29.

## Decision

Retain the generated course site as a public archive and classify the project
as `course-taught` with `operational_state: retired`.

The repository will:

- preserve course sources, the local V2 build, `site/`, public archive URLs,
  Cloudflare configuration, and read-only inspection tools;
- remove automatic external deployment and recurring semester maintenance;
- remove the orphaned dashboard deployment API, its unused JavaScript, and its
  artificial tests;
- remove the state-dependent 2025 orchestration-completion test while retaining
  isolated projection, rule, and pipeline tests; and
- fail closed on manual Cloudflare mutations unless a new owner decision is
  accompanied by `ARCHIVE_REACTIVATION_APPROVED=1`.

The independent Dependabot configuration remains enabled for dependency and
security visibility. It is not a publication path or the retired semester
maintenance workflow; fully ending dependency-update PRs would require a
separate owner decision.

## Consequences

- The existing public site may continue to be served, but repository changes do
  not publish automatically.
- A green local archive build proves reproducibility, not a live deployment.
- Historical reports and generated probe output remain evidence of the 2025
  work and are not current operational authority.
- Existing unrelated lint, partitioned-coverage, and timeout CI debt remains a
  separate maintenance concern.

## Reactivation Gate

Publication may be re-enabled only after a new owner decision confirms all of
the following:

1. the intended Cloudflare account, Pages project, production branch, and
   public-domain behavior;
2. newly authorized credentials stored outside the repository;
3. a reviewed deployment workflow that does not mutate external state from an
   ordinary pull request; and
4. successful local validation and archive build from a clean checkout.
