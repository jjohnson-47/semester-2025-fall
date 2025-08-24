Execute complete Fall 2025 semester preparation workflow with multi-agent coordination.

Usage: /semester-prep "Prepare Fall 2025 semester for launch"

## Workflow Overview

This command orchestrates a comprehensive semester preparation workflow using specialized agents in a coordinated sequence with quality gates between phases.

## Agent Coordination Sequence

### Phase 1: Validation & Quality Assurance

```
orchestrator → qa-validator
```

- Validate all 44+ JSON course files
- Verify RSI compliance for all three courses
- Check date consistency and academic calendar alignment
- Ensure no critical blocking issues exist

**Quality Gate**: All validation must PASS before proceeding

### Phase 2: Content Generation

```
orchestrator → course-content (parallel execution)
├── MATH221 content generation
├── MATH251 content generation
└── STAT253 content generation
```

- Generate syllabi with RSI integration
- Build schedules with platform-specific due dates
- Create weekly materials and supporting content
- Verify template rendering and output quality

**Quality Gate**: All course materials successfully generated

### Phase 3: Calendar Synchronization

```
orchestrator → calendar-sync
```

- Propagate semester dates across all courses
- Resolve any holiday or deadline conflicts
- Generate downloadable .ics calendar files
- Verify no scheduling inconsistencies

**Quality Gate**: Calendar consistency verified

### Phase 4: Deployment Preparation

```
orchestrator → deploy-manager
```

- Build complete static site with all materials
- Configure iframe embedding for Blackboard Ultra
- Set up CORS headers and security policies
- Test all endpoints and embedding functionality

**Quality Gate**: Production deployment ready

### Phase 5: Documentation & Completion

```
orchestrator → docs-keeper
```

- Update all project documentation
- Generate semester preparation reports
- Track decisions and changes made
- Create completion status documentation

**Quality Gate**: All documentation current and complete

## TodoWrite Integration

The orchestrator automatically creates a TodoWrite list to track progress:

1. **Validate all course data** (qa-validator)
2. **Generate updated course materials** (course-content)
3. **Sync calendar dates across courses** (calendar-sync)
4. **Deploy to preview environment** (deploy-manager)
5. **Update orchestration documentation** (docs-keeper)

## Expected Outcomes

### Deliverables

- ✅ All course syllabi generated and verified
- ✅ Course schedules with accurate due dates
- ✅ Iframe-ready materials for Blackboard Ultra
- ✅ Production site deployed and accessible
- ✅ Complete documentation of all changes

### Quality Metrics

- **Validation**: 100% JSON compliance rate
- **Content**: All 3 courses fully prepared
- **Performance**: <2 second load times
- **Accessibility**: WCAG 2.1 AA compliance
- **Integration**: Blackboard iframe compatibility

## Error Handling

If any phase fails, the orchestrator will:

1. Halt progression to prevent cascading failures
2. Report specific error details and recommended fixes
3. Allow manual intervention to resolve issues
4. Resume workflow from the failed phase after resolution

## Execution Time

Expected workflow duration:

- **Phase 1**: 30-60 seconds (validation)
- **Phase 2**: 2-3 minutes (content generation)
- **Phase 3**: 30-60 seconds (calendar sync)
- **Phase 4**: 2-3 minutes (deployment)
- **Phase 5**: 1-2 minutes (documentation)

**Total**: 6-8 minutes for complete semester preparation

## Prerequisites

- All course JSON files must be present and well-formed
- UV environment must be properly configured
- Build dependencies must be installed (`uv sync`)
- Git repository must be in clean state for best results

## Post-Completion Actions

After successful completion:

1. Access dashboard at <http://127.0.0.1:5055>
2. View iframe generator at /embed/generator
3. Test course syllabi at /embed/syllabus/{COURSE}
4. Verify production deployment status

This workflow prepares a complete semester with all quality gates passed and production systems ready for student access.
