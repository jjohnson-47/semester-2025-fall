# ADR 0004: Golden and Contract Testing

- Status: Proposed
- Date: 2025-08-25

## Context
Refactor must preserve behavior; we need safety nets beyond unit tests.

## Decision
- Establish golden tests for normalized outputs and template contexts.
- Establish contract tests (YAML) for policy/date rules and compliance signals.

## Consequences
- Intentional changes require golden updates + justification.
- Contracts document policy guarantees explicitly.

## Implementation Notes
- Semantic HTML diffs for templates; Hypothesis for date boundaries; coverage thresholds enforced in CI.

