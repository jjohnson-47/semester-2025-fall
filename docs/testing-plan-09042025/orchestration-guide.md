# Multi-Agent Test Suite Orchestration Guide

## Your Role: Test Suite Orchestration Lead

You are the orchestration agent responsible for coordinating a parallel test suite implementation across multiple specialized agents. Your mission is to deliver a comprehensive test infrastructure with >70% coverage on critical paths while enabling parallel development across independent tracks.

## Project Context

**Repository:** A Python async task management system with orchestration, prioritization, deployment, and web dashboard components.
**Goal:** Implement risk-weighted test coverage focusing on state machines, cross-process I/O, ranking logic, and schema evolution.
**Timeline:** Aggressive parallel execution with Track 0 as the only blocking dependency.

## Orchestration Strategy

### Phase 1: Foundation (BLOCKING - Must Complete First)
**Track 0 - Shared Infrastructure**
- Single agent assignment
- Estimated time: 2-3 hours
- Creates test helpers all other tracks depend on

### Phase 2: Parallel Execution (Non-blocking)
Launch all tracks simultaneously after Track 0 merges:
- **Track A:** Orchestration & Events (1-2 agents) - HIGHEST PRIORITY
- **Track B:** Deploy API (1 agent) - QUICK WIN
- **Track C:** Prioritization Service (1-2 agents) - HIGH VALUE
- **Track D:** Queue Selection/Solver (1 agent)
- **Track E:** DB Repo & Schema (1 agent)
- **Track F:** HTMX Endpoints (1 agent)
- **Track G:** Views/Main (1 agent)

## Agent Prompts and Instructions

### Track 0: Shared Test Infrastructure Agent

```markdown
You are implementing the shared test infrastructure for our test suite. Your deliverables are:

1. Create `tests/helpers/` directory with:
   - `fake_process.py`: AsyncIO subprocess mock factory that returns scriptable stdout/stderr/returncode
   - `clocks.py`: Time control utilities using freezegun
   - `builders.py`: Task builders and seed graph generators (8-12 tasks, 3 courses, 2 chains)
   - `db.py`: Temporary SQLite repo factory with schema initialization

2. Implement `tests/conftest.py` with fixtures:
   - `tmp_state_dir`: Isolated temp directory per test
   - `frozen_time`: Frozen at Monday 2025-09-01 09:00
   - `repo(tmp_path)`: Returns initialized temp DB with seed data
   - `fake_process_factory()`: Deterministic subprocess mock
   - `event_store_inmemory()` and `event_store_sqlite(tmp_path)`
   - `caplog_debug`: Captures DEBUG level logs

3. Configure pytest:
   - Add markers: unit, integration, property, slow, solver
   - Setup pytest.ini with xdist configuration
   - Create Makefile targets: test-unit, test-integration, test-solver, test-fast

Ensure all helpers are deterministic (seeded RNG, frozen time, no real I/O).
Write at least one sample test using each helper to validate the infrastructure.
```

### Track A: Orchestration & Events Agent

```markdown
You are testing the orchestration and event systems (advanced_orchestrator.py, orchestration_agent.py).

Requirements:
- Target ≥70% coverage on state transitions and event I/O
- Test EventStore: append/load, snapshots, idempotent replays (parametrize in-mem + sqlite)
- Test ReactiveStream: map/filter, backpressure (bounded queue), cancellation
- Test CircuitBreaker: state transitions (CLOSED↔OPEN↔HALF_OPEN), timeouts, failure thresholds
- Test Workflow: execute() happy path, failure → COMPENSATING → FAILED, compensation stack ordering
- Test Coordinator: _handle_task_created spawns and tracks workflows

Use fixtures from Track 0. Assert on state transitions in logs. Ensure no flaky tests.
Create state machine diagram tests that mirror the actual transitions.
```

### Track B: Deploy API Agent

```markdown
You are testing dashboard/api/deploy.py. This is a quick win for coverage.

Requirements:
- Target ≥80% coverage, all branches must be hit
- Mock asyncio.create_subprocess_shell using fake_process_factory from Track 0
- Test scenarios:
  - run_command: happy path, failures, stdout/stderr capture, time budget enforcement
  - build_site: manifest present/missing cases
  - sync_content: handle absent worker directory
  - deploy_worker: parse success tokens correctly
  - verify_deployment: pass/fail conditions
  - execute_full_deployment: orchestration, log ordering, duration aggregation

No real shell calls allowed. All subprocess interactions must use the fake_process_factory.
```

### Track C: Prioritization Service Agent

```markdown
You are testing services/prioritization.py with both unit and property tests.

Requirements:
- Target ≥75% coverage + ≥40% mutation score
- Unit tests:
  - Snapshot rotations and scoring map
  - Constraints: timebox, k limit, min_courses, chain-head requirements
  - explain(task_id) returns stable breakdowns
- Property tests using Hypothesis:
  - Monotonicity: increasing downstream_unlocked never reduces rank
  - Stability under score noise within epsilon bounds
- Integration:
  - refresh_now_queue writes to DB and exports JSON correctly
  - Validate against golden file in tests/golden/

Focus on mathematical correctness and edge cases in ranking logic.
```

### Track D: Queue Selection Solver Agent

```markdown
You are testing tools/queue_select.py (CP-SAT solver).

Requirements:
- Target ≥75% coverage
- Test deterministic small instances:
  - Single heavy task scenarios
  - k capacity constraints
  - Timebox limits
  - Course diversity requirements
  - Tie-breaking logic
- Create regression lock on objective scaling (pre/post int() removal yields same picks)
- Use 'solver' marker for all tests
- Keep runtime ≤2s per test case locally
- Seed all tests for determinism

Focus on solver correctness rather than performance optimization.
```

### Track E: DB Repo & Schema Agent

```markdown
You are testing dashboard/db/repo.py focusing on schema evolution and data integrity.

Requirements:
- Target ≥85% coverage on critical paths
- Test scenarios:
  - Initialize idempotency
  - Optional column alters
  - busy_timeout and PRAGMA propagation
  - JSON import/export round-trip with dependencies and checklists
  - Snapshot writes (best-effort)
  - Error paths: simulated PRAGMA/ALTER failures (should log but not crash)
- Use golden JSON files for validation
- Ensure no global state leakage between tests

Focus on data integrity and graceful error handling.
```

### Track F: HTMX Endpoints Agent

```markdown
You are testing dashboard/api/tasks_htmx.py.

Requirements:
- Target ≥75% coverage
- Test scenarios:
  - quick_add_task: title requirement, lazy DB initialization
  - Status updates produce correct OOB swap fragments
  - view=kanban filtered endpoints return structured keys and grouping
- Assert fragment existence using CSS selectors
- Validate HTMX response headers and swap behaviors
- Test partial template rendering

Focus on HTMX-specific behaviors and fragment correctness.
```

### Track G: Views/Main Agent

```markdown
You are testing dashboard/views/main.py.

Requirements:
- Target ≥75% coverage
- Test scenarios:
  - Basic routes return 200 status
  - Context keys present in templates
  - Template selection under feature flags
  - Error handlers return appropriate JSON vs HTML based on Accept headers
- Ensure no template coupling leaks
- Test flash message handling
- Validate CSRF token presence

Focus on routing logic and template context preparation.
```

## Coordination Checkpoints

### After Track 0 Completion:
1. Verify all fixtures work with sample tests
2. Ensure pytest markers are configured
3. Confirm Makefile targets execute correctly
4. Merge Track 0 before proceeding

### Daily Sync Points:
1. Check coverage metrics per track
2. Identify and resolve any blocking dependencies
3. Share discovered patterns or issues across tracks
4. Update global coverage badge

### Pre-Merge Checklist for Each Track:
- [ ] Markers set and tests runnable in isolation
- [ ] Uses Track 0 shared fixtures exclusively
- [ ] No live subprocess/network/time dependencies
- [ ] Asserts on behavior, not implementation
- [ ] Coverage gate met for module
- [ ] No flaky tests (run 10x to verify)
- [ ] Golden files include update reason if changed

## Success Metrics

### Coverage Targets:
- `advanced_orchestrator.py` family: ≥70%
- `dashboard/api/deploy.py`: ≥80%
- `services/prioritization.py`: ≥75% + property tests
- `tools/queue_select.py`: ≥75%
- `dashboard/db/repo.py`: ≥85%
- HTMX & views: ≥75%

### Quality Gates:
- Zero flaky tests
- Mutation score ≥40% on prioritization & solver (sampled)
- All tests run in <30s locally
- Coverage ratchet: increase thresholds after each green week

## Execution Commands

```bash
# For each track, create a branch and assign to agent:
git checkout -b test/track-0-infrastructure
git checkout -b test/track-a-orchestration
git checkout -b test/track-b-deploy-api
# ... etc

# Run specific track tests:
pytest -m unit tests/unit/test_deploy_api.py
pytest -m solver tests/unit/test_queue_select.py
pytest -m "unit and not solver" -n auto

# Generate coverage reports:
pytest --cov=dashboard.api.deploy --cov-report=html
make cov  # Combined coverage report

# Run mutation testing (weekly):
mutmut run --paths-to-mutate services/prioritization.py
```

## Risk Mitigation

- **Dependency conflicts:** Track 0 must be rock-solid; all agents test against same commit
- **Coverage gaps:** Daily review of combined coverage; reassign agents if needed
- **Flaky tests:** Immediate fix or @pytest.mark.skip with issue number
- **Golden drift:** Lock golden files with hash; explicit UPDATE_GOLDENS=1 protocol

## Communication Protocol

1. Each agent commits frequently with descriptive messages
2. Use PR descriptions that reference this orchestration doc
3. Tag orchestration lead for cross-track issues
4. Update track status in shared tracking doc/board
5. Escalate blockers within 2 hours of discovery

## Launch Sequence

1. **Hour 0:** Assign Track 0 agent, begin infrastructure
2. **Hour 3:** Track 0 PR review and merge
3. **Hour 4:** Launch all parallel tracks (A-G)
4. **Hour 8:** First coverage checkpoint
5. **Hour 16:** Integration and property test additions
6. **Hour 24:** Final coverage aggregation and report

Remember: The goal is not just coverage metrics but meaningful, deterministic tests that catch real bugs and enable confident refactoring. Quality over quantity, but deliver both.
