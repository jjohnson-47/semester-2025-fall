# Multiagent Orchestration Plan: Course Management System Enhancement

## Executive Summary

You are the orchestration agent responsible for coordinating a comprehensive system enhancement across a Course Management System. The repository contains 55 tasks across 3 courses (MATH221, MATH251, STAT253) with a Flask dashboard, SQLite database, and GitHub Actions deployment pipeline.

## Current System State

### Infrastructure
- **Database**: SQLite with 55 tasks, FTS enabled, events tracking
- **Courses**: 3 active (MATH221, MATH251, STAT253), 14 JSON files each, no manifests
- **Pipeline**: 7 GitHub workflows (CI/CD, testing, pages deployment)
- **Dashboard**: Flask-based with HTMX components
- **Git**: Branch `main`, commit `2cc10ee6013aeafd12da54f34a49dba2fea7fb10`

### Key Findings
- ✅ Events table present for audit trail
- ✅ Task management system operational
- ❌ Course manifests missing (0/3 have manifests)
- ❌ Course registry/projection tables absent
- ❌ Test collection empty
- ⚠️ No origin tracking columns in tasks table

## Orchestration Strategy

### Phase 1: System State Analysis (Parallel Execution)
Execute both probe directives simultaneously to establish baseline:

#### Lane A: Repository State Probe
**Priority**: CRITICAL
**Duration**: ~2 minutes
**Output**: `docs/_generated/state_probe.{md,json}`

```bash
# Execute the V2 Repository State & Architecture Probe
# This establishes baseline configuration, database schema, and content inventory
```

#### Lane B: Enrichment Probe  
**Priority**: CRITICAL
**Duration**: ~3 minutes
**Output**: `docs/_generated/plan_input.{md,json}`

```bash
# Execute the V3 Delta-to-Plan Enrichment Probe
# This captures API surfaces, DB introspection, and dependency graphs
```

### Phase 2: Planning Matrix Generation (Sequential)
**Depends on**: Phase 1 completion
**Duration**: ~1 minute

Generate orchestrated work plan based on probe outputs:

```python
import json
import os
from pathlib import Path

def generate_orchestration_matrix():
    """Generate parallelizable work lanes based on system state."""
    
    # Load probe results
    state = json.load(open("docs/_generated/state_probe.json"))
    plan_input = json.load(open("docs/_generated/plan_input.json"))
    
    lanes = []
    
    # Lane 1: Database Evolution
    if not state["db"].get("has_course_projection"):
        lanes.append({
            "id": "db-projection",
            "priority": "HIGH",
            "parallel": True,
            "tasks": [
                "Create course_projection table",
                "Add origin_* columns to tasks",
                "Create projection cache indexes"
            ]
        })
    
    # Lane 2: Course Manifest Generation
    if state["courses"]["course_count"] > 0:
        manifests_needed = [c["course_code"] for c in state["courses"]["courses"] 
                           if not c["has_manifest"]]
        if manifests_needed:
            lanes.append({
                "id": "course-manifests",
                "priority": "HIGH", 
                "parallel": True,
                "tasks": [f"Generate manifest for {code}" for code in manifests_needed]
            })
    
    # Lane 3: Test Infrastructure
    if "empty" in state["test_configuration"]["test_collection_status"]:
        lanes.append({
            "id": "test-setup",
            "priority": "MEDIUM",
            "parallel": False,
            "tasks": [
                "Create test fixtures",
                "Write API endpoint tests",
                "Add dashboard UI tests"
            ]
        })
    
    # Lane 4: Performance Optimization
    db_introspection = plan_input.get("db", {})
    if not db_introspection.get("hot_index_present", {}).get("status"):
        lanes.append({
            "id": "db-performance",
            "priority": "MEDIUM",
            "parallel": True,
            "tasks": [
                "Add index on tasks.status",
                "Add index on tasks.course",
                "Add index on tasks.due_at"
            ]
        })
    
    return {"lanes": lanes, "total_tasks": sum(len(l["tasks"]) for l in lanes)}
```

### Phase 3: Parallel Execution Lanes

Based on probe results, execute these lanes in parallel:

#### Lane 1: Database Schema Evolution
**Can Run**: Immediately
**Dependencies**: None
```sql
-- Add projection support
CREATE TABLE IF NOT EXISTS course_projection (
    course_code TEXT PRIMARY KEY,
    projection JSON,
    updated_at TIMESTAMP
);

-- Add origin tracking
ALTER TABLE tasks ADD COLUMN origin_ref TEXT;
ALTER TABLE tasks ADD COLUMN origin_kind TEXT;
ALTER TABLE tasks ADD COLUMN origin_version INTEGER;
```

#### Lane 2: Course Content Standardization  
**Can Run**: Immediately
**Dependencies**: None
```python
# Generate manifests for each course
for course in ["MATH221", "MATH251", "STAT253"]:
    manifest = {
        "$schema": "v1",
        "course_code": course,
        "items": analyze_course_items(f"content/courses/{course}")
    }
    save_manifest(course, manifest)
```

#### Lane 3: API & HTMX Testing
**Can Run**: After Lane 1
**Dependencies**: Database schema updates
```python
# Test critical API endpoints
endpoints = extract_endpoints("docs/_generated/api_routes.json")
for endpoint in endpoints:
    create_test(endpoint)
```

#### Lane 4: Deploy Pipeline Validation
**Can Run**: Immediately  
**Dependencies**: None
```bash
# Validate deploy.py surface area
python dashboard/api/deploy.py --dry-run
```

## Execution Commands

### For Claude Code CLI

```bash
# Step 1: Initialize and run probes
claude-code --task "Execute the Repository State Probe (V2) directive from the provided documentation. Commit results to docs/_generated/."

# Step 2: Run enrichment probe  
claude-code --task "Execute the Delta-to-Plan Enrichment Probe (V3) directive. Commit results to docs/_generated/."

# Step 3: Generate orchestration matrix
claude-code --task "Generate orchestration matrix from probe outputs. Create parallel work lanes based on system gaps."

# Step 4: Execute lanes in parallel (spawn sub-agents)
claude-code --task "Execute Lane 1: Database Schema Evolution" &
claude-code --task "Execute Lane 2: Course Content Standardization" &
claude-code --task "Execute Lane 3: Deploy Pipeline Validation" &
wait

# Step 5: Execute dependent lanes
claude-code --task "Execute Lane 3: API & HTMX Testing"
```

## Success Criteria

### Phase 1 Complete When:
- [x] `state_probe.json` exists with valid data
- [x] `plan_input.json` exists with valid data
- [x] `db_introspection.json` shows table structures
- [x] `task_graph.dot` visualizes dependencies

### Phase 2 Complete When:
- [ ] All course manifests exist (3/3)
- [ ] Database has projection tables
- [ ] Tasks have origin columns
- [ ] Indexes exist on hot columns

### Phase 3 Complete When:
- [ ] Test suite runs successfully
- [ ] API endpoints have coverage
- [ ] Deploy script validates
- [ ] Dashboard loads without errors

## Probe Directives

### Directive 1: Repository State Probe (V2)
[Include full V2 probe directive here - from document 2]

### Directive 2: Enrichment Probe (V3)  
[Include full V3 probe directive here - from document 3]

## Notes for Orchestrator

1. **Parallelization**: Lanes marked `parallel: true` can run simultaneously
2. **Checkpointing**: Commit after each lane completes
3. **Failure Handling**: If a lane fails, continue others but mark dependency chains as blocked
4. **Communication**: Use `docs/_generated/orchestration_status.json` for inter-agent coordination
5. **Progress Tracking**: Update status file with:
   ```json
   {
     "phase": 1-3,
     "lanes_complete": ["lane-id"],
     "lanes_active": ["lane-id"],
     "lanes_blocked": ["lane-id"],
     "timestamp": "ISO-8601"
   }
   ```

## Resource Allocation

- **Probe Execution**: 1 agent, sequential
- **Lane Execution**: Up to 4 parallel agents
- **Validation**: 1 agent for final checks
- **Total Agents Needed**: 5-6 for optimal parallelization

---

*This orchestration plan is designed for execution via Claude Code CLI with multiagent coordination. Each lane can be assigned to a separate agent for parallel execution, with the orchestrator managing dependencies and checkpoints.*
