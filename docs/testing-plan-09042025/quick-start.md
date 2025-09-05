# Test Suite Orchestration: Quick Start

## Immediate Actions for Orchestration Agent

### Step 1: Initialize Infrastructure (Hour 0)

```bash
# Create foundation branch and start Track 0
claude-code "You are implementing Track 0 test infrastructure. Create tests/helpers/ with fake_process.py, clocks.py, builders.py, and db.py. Implement tests/conftest.py with all fixtures listed in the requirements. Configure pytest markers and Makefile targets. Use the detailed requirements from the orchestration guide."

# Review and merge Track 0 (Hour 3)
git checkout main
git pull
git merge test/track-0-infrastructure
```

### Step 2: Launch Parallel Tracks (Hour 4)

Open 7 terminal windows/sessions and run simultaneously:

```bash
# Terminal 1 - Track A (Highest Priority)
claude-code "Test advanced_orchestrator.py and orchestration_agent.py. Target 70% coverage on state transitions. Test EventStore, ReactiveStream, CircuitBreaker, Workflow, and Coordinator. Use Track 0 fixtures. Refer to orchestration guide for full requirements."

# Terminal 2 - Track B (Quick Win) 
claude-code "Test dashboard/api/deploy.py. Target 80% coverage. Mock all subprocess calls with fake_process_factory. Test run_command, build_site, sync_content, deploy_worker, verify_deployment, execute_full_deployment. No real shell calls."

# Terminal 3 - Track C (High Value)
claude-code "Test services/prioritization.py with unit and property tests. Target 75% coverage. Test snapshot rotations, scoring, constraints. Add Hypothesis property tests for monotonicity and stability. Include integration test for refresh_now_queue."

# Terminal 4 - Track D
claude-code "Test tools/queue_select.py CP-SAT solver. Target 75% coverage. Test deterministic small instances, constraints, tie-breaking. Add regression locks. Use 'solver' marker. Keep tests under 2s each."

# Terminal 5 - Track E  
claude-code "Test dashboard/db/repo.py. Target 85% coverage. Test schema evolution, JSON import/export, error paths. Use golden files for validation. No global state leaks."

# Terminal 6 - Track F
claude-code "Test dashboard/api/tasks_htmx.py. Target 75% coverage. Test quick_add_task, status updates, kanban views. Assert on HTMX fragments using CSS selectors."

# Terminal 7 - Track G
claude-code "Test dashboard/views/main.py. Target 75% coverage. Test routes, context keys, template selection, error handlers."
```

### Step 3: Monitor Progress (Every 4 hours)

```bash
# Check individual track coverage
pytest --cov=advanced_orchestrator --cov-report=term tests/unit/test_advanced_orchestrator.py
pytest --cov=dashboard.api.deploy --cov-report=term tests/unit/test_deploy_api.py
# ... repeat for each module

# Generate combined coverage report
pytest --cov=. --cov-report=html tests/
open htmlcov/index.html

# Run all fast tests
make test-fast

# Check for flaky tests
pytest-randomly --randomly-seed=1234 tests/unit/ --count=10
```

### Step 4: Integration Checkpoint (Hour 16)

```bash
# After unit tests are green, add integration tests
claude-code "Create tests/integration/test_workflow_paths.py. Test end-to-end workflows across orchestrator, prioritization, and deploy components. Use Track 0 fixtures."

claude-code "Create tests/integration/test_api_crud_and_stats.py. Test complete CRUD operations and statistics generation across API endpoints."
```

### Step 5: Quality Gates (Hour 20)

```bash
# Run mutation testing on critical modules
mutmut run --paths-to-mutate services/prioritization.py --runner="pytest tests/unit/test_prioritization_service.py"
mutmut run --paths-to-mutate tools/queue_select.py --runner="pytest tests/unit/test_queue_select.py"

# Check for determinism
PYTHONHASHSEED=0 pytest tests/
PYTHONHASHSEED=42 pytest tests/
# Results should be identical

# Verify markers work
pytest -m unit --co
pytest -m integration --co
pytest -m solver --co
```

### Step 6: Final Merge Sequence (Hour 24)

```bash
# Merge in dependency order
git checkout main
git merge test/track-b-deploy-api     # Quick win first
git merge test/track-c-prioritization  # High value second
git merge test/track-a-orchestration   # Highest priority third
git merge test/track-d-solver
git merge test/track-e-db-repo
git merge test/track-f-htmx
git merge test/track-g-views

# Run full test suite
make test
make cov

# Generate coverage badge
coverage-badge -o coverage.svg
```

## Critical Reminders

1. **Track 0 MUST complete first** - It's the only blocking dependency
2. **No real I/O in tests** - Use fakes/mocks from Track 0
3. **Deterministic always** - Frozen time, seeded RNG, no network
4. **Flaky tests = immediate fix** - Don't hide with reruns
5. **Coverage is risk-weighted** - Focus on state machines and critical paths

## Emergency Escalation

If blocked for >2 hours on any track:
1. Check if it's a Track 0 fixture issue (fix there first)
2. Simplify test scope (can always add more later)
3. Mark as @pytest.mark.skip with TODO and continue
4. Document blocker in PR description for follow-up

## Success Criteria Checklist

- [ ] Track 0 merged and all fixtures working
- [ ] All 7 parallel tracks have >50% coverage
- [ ] Priority modules meet their specific targets
- [ ] Zero flaky tests across 10 runs
- [ ] Combined coverage >70% overall
- [ ] All markers functional
- [ ] Make targets working
- [ ] Mutation testing >40% on prioritization/solver
- [ ] Integration tests passing
- [ ] Golden files validated
