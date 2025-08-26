# ADR 0002: Central Date Authority

- Status: Proposed
- Date: 2025-08-25

## Context
Date logic exists across builders and templates, risking inconsistencies (weekend due dates, holiday shifts).

## Decision
- Implement `DateRules` as the sole authority for due-date computation within a rules engine.
- Builders and templates must consume pre-computed dates; no date math in templates.

## Consequences
- Single source for date policies; easier testing via contracts and property tests.
- Requires context projection changes for templates.

## Implementation Notes
- Consume `SemesterCalendar` and encode “no weekend dues” and holiday shift logic.

