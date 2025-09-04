# Orchestration Plan (V2 Integration)

This document supersedes the pre-refactor plan by aligning the staged build pipeline and date authority with the current V2 architecture.

## Goals

- Preserve the 6-stage pipeline (validate → normalize → project → generate → package → report) while integrating with V2 services/builders.
- Unify date rules under the rules engine with assignment-type preferences, holiday handling, and shift provenance.
- Provide compatibility shims so feature branches can merge cleanly without duplicating architecture.

## Implemented

- Enhanced pipeline in `scripts/build_pipeline.py` with per-stage CLI, verbose/dry-run, manifests, and reports.
- Compatibility wrapper `scripts/build_pipeline_impl.py` (re-exports upgraded pipeline class and CLI).
- Unified date rules (`scripts/rules/dates.py`) with preferences, holiday shifts, and provenance logging.
- Compatibility facade `scripts/rules/dates_full.py` for pre-refactor imports.
- Schema migrator compat at `scripts/schema/migrator.py` delegating to current migrations.
- v1.1.0 helper re-export at `scripts/utils/schema/versions/v1_1_0.py`.

## Orchestrated Workflow

- `make orchestrate -j3` runs validation, pipeline, and tests in parallel.
- Reports: `build/reports/build_summary.json`, `build/reports/build_report.md`.
- Manifests: per-course under `build/manifests/`, global under `build/package/manifest.json`.

## Merge Strategy

1. Land compatibility shims (done) to avoid breaking imports from feature branches.
2. Merge `feat/build-pipeline` and `feat/date-authority` into `main` (no behavioral change, just code history consolidation).
3. Retain wrappers for a deprecation window; point new work to consolidated modules.

## Next

- Optionally remove compatibility wrappers once downstream references are updated.

# Multi-Agent Orchestration Plan
## Refactor Execution - August 25, 2025

**Orchestrator Lead:** Active  
**Status:** Phase 0 - Pre-flight  
**Target Completion:** September 2-4, 2025 (6-8 working days)

---

## Current Status Dashboard

### Active Workstreams (Parallel Execution)
| Agent | Workstream | Status | Branch | Dependencies | Quality Gate |
|-------|------------|--------|--------|--------------|--------------|
| A1 | Schema & Migration | 🟡 Ready | feat/schema-migration | None | ✅ Ready |
| A2 | Rules Engine | 🟡 Ready | feat/rules-engine | None | ✅ Ready |
| A3 | Date Authority | 🟡 Ready | feat/date-authority | None | ✅ Ready |
| A4 | Service Layer | ⏸️ Blocked | - | A1, A2 | ⏳ Waiting |
| A5 | Build Pipeline | 🟡 Ready | feat/build-pipeline | Soft-dep A4 | ✅ Ready |
| A6 | Template Migration | 🟡 Ready | feat/template-migration | A4 (later) | ✅ Ready |
| A7 | Builders Integration | ⏸️ Blocked | - | A4 | ⏳ Waiting |
| A8 | Dashboard Integration | ⏸️ Blocked | - | A4 | ⏳ Waiting |
| A9 | QA & Tooling | 🟡 Ready | feat/qa-tooling | None | ✅ Ready |
| A10 | Docs & CM | 🟡 Ready | feat/docs-cm | None | ✅ Ready |

### Phase Timeline
- **Phase 0** (Today): Pre-flight setup ✅
- **Phase 1** (Day 1-2): Data Foundation - A1, A3 parallel
- **Phase 2** (Day 2-3.5): Rules Engine + Models - A2, A3, A9
- **Phase 3** (Day 3.5-5): Service Layer + Pipeline - A4, A5
- **Phase 4** (Day 5-6): Template & Builders - A6, A7
- **Phase 5** (Day 6-7): Dashboard Integration - A8
- **Phase 6** (Day 7-8): QA Hardening & Cutover - A9, A10

---

## Workstream Charters

### A1: Schema & Migration Agent
**Mission:** Implement v1.1.0 schemas with stable IDs and migration tools  
**Deliverables:**
- `scripts/utils/schema/versions/v1_1_0.py`
- `scripts/schema/migrator.py`
- `scripts/migrations/add_stable_ids.py`
- Migrated JSON fixtures with `_meta` headers
- Tests with ≥85% coverage

**Quality Gates:**
- Schema validation passes on all course JSON
- Migrator runs in dry-run mode successfully
- No data loss in migration
- Backward compatibility maintained

### A2: Rules Engine Agent
**Mission:** Build normalized models with provenance tracking  
**Deliverables:**
- `scripts/rules/models.py` - NormalizedCourse/Field dataclasses
- `scripts/rules/engine.py` - CourseRulesEngine with rule protocol
- Unit tests for normalization
- Provenance tracking implementation

**Quality Gates:**
- Deterministic normalization across runs
- Type safety with mypy --strict
- Provenance chain complete for all fields

### A3: Date Authority Agent
**Mission:** Centralize all date rules and holiday handling  
**Deliverables:**
- `scripts/rules/dates.py` - DateRules implementation
- No-weekend policy enforcement
- Holiday shift logic (Labor Day, Thanksgiving, etc.)
- Property tests with Hypothesis
- Contract tests in YAML

**Quality Gates:**
- No due dates on weekends
- Holiday shifts properly applied
- Contract tests pass
- Property tests cover edge cases

### A4: Service Layer Agent
**Mission:** Unified service interfaces with caching and validation  
**Deliverables:**
- `scripts/services/course_service.py` - CourseService
- `scripts/services/validation.py` - ValidationGateway
- `scripts/services/changes.py` - ChangeDetector
- Cache key implementation
- Fingerprint-based change detection

**Quality Gates:**
- Cache invalidation works correctly
- Validation aggregates all errors
- Change detection accurate
- ≥85% test coverage

### A5: Build Pipeline Agent
**Mission:** Staged, deterministic build pipeline  
**Deliverables:**
- `scripts/build_pipeline.py` - Main pipeline
- Stage implementations (validate, normalize, project, generate, package, report)
- Per-course reports in `build/reports/`
- Build manifests
- CLI interface

**Quality Gates:**
- Pipeline runs end-to-end
- Reports generated correctly
- Deterministic outputs
- Idempotent stages

### A6: Template Migration Agent
**Mission:** Remove logic from templates, use projections  
**Deliverables:**
- Refactored templates in `templates/`
- Context projection code
- Golden snapshots for template contexts
- Documentation of changes

**Quality Gates:**
- Templates contain no logic
- Visual parity maintained
- Golden tests pass
- HTML semantic diffs acceptable

### A7: Builders Integration Agent
**Mission:** Adapt builders to consume service projections  
**Deliverables:**
- Updated `build_syllabi.py`
- Updated `build_schedules.py`
- Updated `build_bb_packages.py`
- CLI compatibility maintained
- Feature flags for transition

**Quality Gates:**
- CLI interface unchanged
- Output parity with legacy
- Feature flags work
- Integration tests pass

### A8: Dashboard Integration Agent
**Mission:** Intelligence view and state management  
**Deliverables:**
- `dashboard/services/task_intelligence.py`
- `dashboard/state/manager.py`
- Updated routes in `app.py`
- Tests for new services

**Quality Gates:**
- Dashboard remains stable
- Intelligence data populates
- State snapshots work
- API compatibility maintained

### A9: QA & Tooling Agent
**Mission:** Comprehensive test coverage and tooling  
**Deliverables:**
- Contract tests in `tests/contracts/`
- Golden tests in `tests/golden/`
- Property tests with Hypothesis
- Coverage configuration
- Pre-commit hooks
- CI matrix updates

**Quality Gates:**
- ≥85% coverage on changed code
- All test types implemented
- CI pipeline green
- No security issues (bandit)

### A10: Docs & Change Management Agent
**Mission:** Complete documentation and migration guides  
**Deliverables:**
- ADRs in `docs/adr/`
- Migration guide
- Updated READMEs
- Architecture diagrams
- Developer runbooks

**Quality Gates:**
- All ADRs complete
- Diagrams accurate
- Migration guide tested
- Documentation reviewed

---

## Coordination Protocol

### Daily Sync Points
- **09:00**: Status check - all agents report blockers
- **14:00**: Progress update - completed items
- **17:00**: Next-day planning - dependencies resolved

### Communication Channels
- **Blocking Issues**: Create with `blocking` label
- **Cross-team Dependencies**: Use `depends-on:#PR` labels
- **Status Updates**: Comment on workstream issues

### Quality Gate Enforcement
Each PR must pass:
1. `make validate` - JSON validation
2. `ruff format --check` - Code formatting
3. `ruff check` - Linting
4. `mypy --strict` - Type checking
5. `pytest` with ≥85% coverage
6. Contract tests (if applicable)
7. Golden tests (if applicable)

### Merge Protocol
1. PRs reviewed by Orchestrator Lead
2. Dependencies verified via DAG
3. Quality gates green
4. Merge in dependency order
5. Integration tests after each merge

---

## Risk Register

| Risk | Impact | Mitigation | Owner |
|------|--------|------------|-------|
| Schema migration breaks data | High | Dry-run first, backup fixtures | A1 |
| Template changes break visuals | Medium | Golden tests, visual diffs | A6 |
| Dashboard instability | High | Feature flags, minimal changes | A8 |
| Timeline slip | Medium | Add agents to critical path | Lead |
| Test flakiness | Low | Retry logic, deterministic seeds | A9 |

---

## Success Criteria

### Phase 0 Complete ✅
- [x] Scaffolding in place
- [x] CI configured
- [x] ADRs drafted
- [x] Issues created
- [x] Branches ready

### Phase 1-6 (In Progress)
- [ ] All workstreams complete
- [ ] Quality gates passing
- [ ] Documentation complete
- [ ] Integration tests green
- [ ] Performance acceptable

### Final Acceptance
- [ ] Full pipeline runs successfully
- [ ] Dashboard stable
- [ ] All tests passing
- [ ] Documentation reviewed
- [ ] Rollback plan tested

---

## Next Actions (Immediate)

1. **Create feature branches** for each ready workstream
2. **Assign agents** to workstreams (or simulate via focused work)
3. **Start Phase 1** parallel execution:
   - A1: Begin schema v1.1.0 implementation
   - A3: Implement DateRules
   - A9: Set up test harness
   - A10: Begin ADR drafting

4. **Set up monitoring**:
   - GitHub project board
   - CI status dashboard
   - Coverage tracking

---

**Orchestrator Notes:**
- Maximum parallelism: 7 agents can work simultaneously
- Critical path: A1 → A4 → A7/A8 (must optimize)
- Daily checkpoint at 14:00 to assess progress
- Escalation path: Add agents to blocked work

---

**Document Version:** 1.0  
**Last Updated:** August 25, 2025 20:00  
**Next Review:** August 26, 2025 09:00
