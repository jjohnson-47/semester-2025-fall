---
name: Agent Workstream
about: Plan and track a parallel refactor lane with clear checkpoints
title: "[Workstream] <area>: <short goal>"
labels: [refactor, agent, parallel]
assignees: 
---

## Summary

- Goal:
- Owner(s):
- Dependencies:
- Deliverables:

## Scope

- In scope:
- Out of scope:

## Plan

- [ ] Create feature branch `feat/<area>`
- [ ] Add ADR (if applicable)
- [ ] Write/upate schemas/interfaces
- [ ] Implement modules
- [ ] Unit tests (≥85% for changed files)
- [ ] Contract tests (if applicable)
- [ ] Golden tests (if applicable)
- [ ] Type check passes (`mypy --strict`)
- [ ] Lint/format passes (`ruff format && ruff check`)
- [ ] Docs updated

## Risks & Mitigations

- Risk:
- Mitigation:

## Review Checklist

- [ ] Backwards-compat maintained or gated
- [ ] Clear migration path documented
- [ ] Deterministic outputs validated

