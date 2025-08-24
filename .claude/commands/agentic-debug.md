Multi-agent debugging workflow for semester management system issues.

Usage: /agentic-debug "Fix validation errors in MATH221 schedule"

## Debugging Workflow

This command coordinates multiple specialist agents to quickly identify and resolve complex issues in the semester management system.

## Agent Investigation Sequence

### Phase 1: Issue Analysis

```
orchestrator → qa-validator (primary investigator)
```

- Run comprehensive validation to identify all issues
- Categorize problems by severity and impact
- Check for related issues across courses
- Generate detailed error analysis

### Phase 2: Parallel Investigation

```
orchestrator spawns parallel agents:
├── qa-validator → JSON schema violations
├── course-content → Template and generation issues
├── calendar-sync → Date and schedule conflicts
└── deploy-manager → Build and deployment problems
```

Each specialist investigates their domain:

- **qa-validator**: Data integrity, compliance, validation failures
- **course-content**: Template errors, content generation issues
- **calendar-sync**: Date conflicts, calendar inconsistencies
- **deploy-manager**: Build failures, deployment issues, iframe problems

### Phase 3: Root Cause Analysis

```
orchestrator → aggregates findings
```

- Combine investigation results from all agents
- Identify root cause vs. symptom issues
- Determine fix priority and dependencies
- Plan resolution strategy

### Phase 4: Fix Implementation

```
orchestrator → appropriate specialist agent
```

Route to the agent best suited to implement the fix:

- **JSON issues** → qa-validator + Edit tools
- **Content problems** → course-content + template updates
- **Date conflicts** → calendar-sync + schedule adjustments
- **Build issues** → deploy-manager + configuration fixes

### Phase 5: Verification

```
orchestrator → qa-validator (final verification)
```

- Re-run validation to confirm fix
- Test affected functionality end-to-end
- Verify no new issues introduced
- Document resolution for future reference

## Common Debug Scenarios

### JSON Validation Failures

**Symptoms**: `make validate` fails, schema violations
**Primary Agent**: qa-validator
**Parallel Checks**:

- course-content (template compatibility)
- calendar-sync (date format issues)

### Content Generation Issues

**Symptoms**: Missing syllabi, template errors, build failures
**Primary Agent**: course-content
**Parallel Checks**:

- qa-validator (source data validation)
- deploy-manager (output verification)

### Calendar/Date Conflicts

**Symptoms**: Due dates outside semester, holiday conflicts
**Primary Agent**: calendar-sync
**Parallel Checks**:

- qa-validator (data consistency)
- course-content (template date handling)

### Deployment Problems

**Symptoms**: Site build failures, iframe not working, CORS errors
**Primary Agent**: deploy-manager
**Parallel Checks**:

- course-content (source material verification)
- qa-validator (pre-deployment checks)

## Investigation Commands

Each agent uses specialized diagnostic commands:

### qa-validator

```bash
make validate --verbose
python scripts/validate_json.py --detailed
python scripts/check_rsi_compliance.py --all
python scripts/verify_dates.py --conflicts
```

### course-content

```bash
python scripts/build_syllabi.py --debug
python scripts/test_templates.py --course MATH221
make syllabi VERBOSE=1
```

### calendar-sync

```bash
python scripts/utils/semester_calendar.py --verify
python scripts/check_due_dates.py --conflicts
```

### deploy-manager

```bash
make site --debug
python site_build.py --verbose
curl -I http://127.0.0.1:5055/embed/syllabus/MATH221
```

## Rapid Resolution Patterns

### Quick Fix Workflow

1. **Identify** (orchestrator assigns primary agent)
2. **Isolate** (parallel investigation by specialists)
3. **Fix** (targeted resolution by appropriate agent)
4. **Verify** (qa-validator confirms resolution)

### Complex Issue Workflow

1. **Deep Analysis** (think hard with multiple agents)
2. **Sequential Investigation** (follow dependency chain)
3. **Coordinated Fix** (multiple agents working together)
4. **Comprehensive Testing** (full system verification)

## Error Recovery

If debugging reveals systemic issues:

1. **Rollback Option**: Restore from last known good state
2. **Incremental Fix**: Address issues one at a time
3. **Full Rebuild**: Complete regeneration if corruption detected
4. **Emergency Mode**: Minimal viable system for urgent deadlines

## Performance Optimization

- Use **Haiku model** for simple validation checks
- Use **Sonnet model** for content fixes and rebuilds
- Use **Opus model** for complex system analysis
- Parallel execution where issues are independent

## Documentation

All debug sessions automatically generate:

- **Issue Report**: What was wrong and how it was detected
- **Resolution Log**: Steps taken to fix the problem
- **Prevention Notes**: How to avoid similar issues
- **System Impact**: What was affected and how it was verified

This workflow provides rapid issue identification and resolution with minimal manual intervention required.
