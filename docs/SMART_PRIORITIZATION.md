# Smart Task Prioritization System Documentation

## Overview

The Smart Task Prioritization System is an intelligent task management engine that goes beyond simple due dates to identify the most impactful work in complex, interdependent course preparation workflows. It combines critical chain analysis, dependency resolution, and phase-aware optimization to reduce decision fatigue and ensure critical path work gets done first.

## Core Concepts

### 1. Smart Score

Each task receives a composite `smart_score` calculated from multiple weighted factors:

```
smart_score = Σ(coefficient × factor_value)
```

The factors include:
- **Base Priority** (α): Traditional due date urgency
- **Critical Chain Weight** (β): Sum of weights along path to anchors
- **Unblock Impact** (γ): Number of downstream tasks freed
- **Anchor Proximity** (δ): Inverse distance to key milestones
- **Chain Head Boost** (ε): Bonus for immediately actionable tasks
- **Phase Adjustment** (ζ): Category bias based on semester phase

### 2. Chain Heads

Tasks are marked as "chain heads" (displayed with ➜) when:
- Status is `todo` (ready to work)
- All dependencies are `done` (nothing blocking)
- They represent the next actionable step in a dependency chain

Chain heads receive a significant scoring boost because starting them immediately progresses the critical path.

### 3. Anchors

Anchors are milestone tasks that represent major completion points. The system identifies paths to these anchors to understand which work contributes most directly to key objectives:

- `COURSE-READY`: Course fully prepared for students
- `OPEN-COURSE`: Course available to students
- `QA-STUDENT-PREVIEW`: Quality assurance complete

### 4. Phases

The system recognizes different semester phases and adjusts priorities accordingly:

#### Pre-Launch Phase (-30 to -8 days)
Focus on infrastructure and content creation:
- Setup tasks: 5.0x boost
- Technical tasks: 4.0x boost
- Materials: 3.0x boost

#### Launch Week (-7 to 0 days)
Final preparations and testing:
- Technical tasks: 5.0x boost
- Assessment setup: 4.0x boost
- Communication prep: 3.0x boost

#### Week One (1 to 7 days)
Active semester support:
- Communication: 5.0x boost
- Technical support: 3.0x boost
- Assessment delivery: 2.0x boost

#### In-Term (8+ days)
Steady-state operations:
- Assessment: 3.0x boost
- Communication: 2.5x boost
- Content updates: 2.0x boost

## Configuration

### Priority Contracts (`priority_contracts.yaml`)

The entire prioritization strategy is tunable through the contracts file:

```yaml
coefficients:
  alpha_due: 1.0        # Due date weight
  beta_critical: 2.5    # Critical chain weight
  gamma_impact: 3.0     # Unblock impact weight
  delta_proximity: 1.5  # Anchor proximity weight
  epsilon_head: 10.0    # Chain head boost
  zeta_phase: 0.5       # Phase adjustment weight
```

Adjust these coefficients to change the system's behavior:
- Increase `beta_critical` to focus more on critical path
- Increase `gamma_impact` to prioritize high-unblock tasks
- Increase `alpha_due` to make deadlines more important

### Now Queue Settings

Control the focused task list presentation:

```yaml
now_queue:
  max_items: 7              # Total tasks to show
  per_course_limit: 3       # Max per course
  ensure_each_course: true  # Guarantee course coverage
  chain_head_preference: 1.2 # 20% boost for chain heads
```

### Pinning Tasks

Force specific tasks to the top during critical periods:

```yaml
pins:
  by_id:
    - "MATH221-2025F-SYLLABUS-GENERATE"
  by_suffix:
    - "ROSTER-ROLES"  # All roster checks
  pin_boost: 100.0    # Massive score boost
```

## Algorithm Details

### Critical Chain Calculation

The system computes the critical chain weight by:
1. Starting from the task
2. Following all paths to anchor tasks
3. Summing weights along the heaviest path
4. Applying distance decay (default 0.95 per hop)

```python
def compute_chain_weight(task_id, anchors):
    # BFS to find paths to all anchors
    best_weight = 0
    for path in find_paths_to_anchors(task_id, anchors):
        path_weight = sum(task.weight for task in path)
        adjusted = path_weight * (decay ** len(path))
        best_weight = max(best_weight, adjusted)
    return best_weight
```

### Unblock Impact Analysis

For each task, the system counts all downstream blocked tasks:

```python
def get_blocked_descendants(task_id):
    descendants = set()
    queue = [task_id]
    while queue:
        current = queue.pop()
        for dependent in get_dependents(current):
            if dependent.status == "blocked":
                descendants.add(dependent)
            queue.append(dependent)
    return len(descendants)
```

### Phase Detection

The system automatically detects the current phase based on days relative to semester start:

```python
def get_current_phase():
    days_since_start = (today - semester_start).days
    for phase in phases:
        if phase.start_days <= days_since_start <= phase.end_days:
            return phase
```

## Usage

### Running Prioritization

```bash
# Basic prioritization
python dashboard/tools/reprioritize.py \
  --tasks dashboard/state/tasks.json \
  --contracts dashboard/tools/priority_contracts.yaml \
  --semester-first-day 2025-08-25 \
  --write

# Preview without writing
python dashboard/tools/reprioritize.py \
  --tasks dashboard/state/tasks.json \
  --contracts dashboard/tools/priority_contracts.yaml \
  --semester-first-day 2025-08-25

# Show only Now Queue
python dashboard/tools/reprioritize.py \
  --tasks dashboard/state/tasks.json \
  --contracts dashboard/tools/priority_contracts.yaml \
  --semester-first-day 2025-08-25 \
  --now-queue-only
```

### Output Files

The system generates two files:

1. **Updated `tasks.json`**: Original tasks enhanced with:
   - `smart_score`: Calculated priority score
   - `is_chain_head`: Boolean for chain head status
   - `chain_anchor`: ID of nearest anchor
   - `chain_distance`: Hops to anchor
   - `unblock_count`: Number of tasks this unblocks
   - `score_breakdown`: Detailed scoring components

2. **`now_queue.json`**: Focused task list containing:
   - Top 3-7 most important tasks
   - Metadata about current phase
   - Total actionable task count

## Dashboard Integration

The dashboard automatically uses smart scores when available:

### Visual Indicators
- **➜** Chain head marker (immediately actionable)
- **Score badges** showing smart_score value
- **Unblock counts** showing downstream impact
- **Anchor paths** showing milestone connection

### Now Queue Display
The Now Queue appears prominently at the top of the dashboard with:
- Task title and course
- Smart score
- Unblock count
- One-click "Start" button
- Brief description

### Sorting
All task lists sort by `smart_score` descending, ensuring high-impact work naturally floats to the top.

## Tuning Guide

### For Different Work Styles

#### "Deadline Driven"
Increase due date weight:
```yaml
coefficients:
  alpha_due: 3.0  # Triple due date importance
```

#### "Unblock Everything"
Prioritize freeing up work:
```yaml
coefficients:
  gamma_impact: 5.0  # Heavily weight unblocking
```

#### "Critical Path Focus"
Emphasize chain progression:
```yaml
coefficients:
  beta_critical: 4.0   # Increase chain weight
  epsilon_head: 20.0   # Double chain head boost
```

### For Different Phases

#### Summer Prep (Early Start)
Extend pre-launch phase:
```yaml
phases:
  prelaunch:
    start_days: -60  # Start 2 months early
    end_days: -8
```

#### Compressed Timeline
Shorten phases and increase urgency:
```yaml
phases:
  prelaunch:
    start_days: -14  # Only 2 weeks prep
  launch_week:
    start_days: -3   # 3-day launch
```

## Troubleshooting

### Common Issues

**All tasks have similar scores**
- Increase coefficient differentiation
- Check that dependencies are properly set
- Verify anchor tasks are identified

**Wrong tasks appearing in Now Queue**
- Check phase detection (days calculation)
- Review category boosts for current phase
- Verify task statuses are correct

**Chain heads not detected**
- Ensure dependencies use correct task IDs
- Check that prerequisite tasks are marked `done`
- Verify task status is `todo` (not `blocked`)

### Debugging

Enable verbose output:
```yaml
debug:
  verbose_scoring: true
  score_log_file: "dashboard/logs/scoring.log"
  include_score_breakdown: true
```

This adds `score_breakdown` to each task showing individual factor contributions.

## Advanced Features

### Staleness Penalty

Penalize tasks that sit in `todo` too long:

```yaml
staleness:
  enabled: true
  days_until_stale: 14
  stale_penalty: -5.0
  max_penalty: -50.0
```

### Optional LLM Re-ranking

For experimental AI-assisted prioritization:

```yaml
llm_rerank:
  enabled: true
  model: "gpt-4o-mini"
  max_candidates: 20
```

The LLM reviews top candidates and can re-order based on semantic understanding, but the DAG validation ensures it never violates dependencies.

## Performance Considerations

The system efficiently handles:
- 500+ tasks with sub-second scoring
- Complex dependency graphs (100+ edges)
- Real-time re-prioritization on status changes

For very large task sets (1000+), consider:
- Increasing the distance decay factor
- Limiting chain depth calculation
- Caching anchor paths between runs

## Future Enhancements

Planned improvements include:
- Multi-user task assignment and workload balancing
- Time estimation and capacity planning
- Historical velocity tracking
- Predictive completion dates
- Integration with calendar systems
- Mobile app companion

## Support

For issues or questions:
- Review score breakdowns in task data
- Check phase detection matches expected timeline
- Verify dependency chains with dashboard visualization
- Adjust coefficients incrementally and test

The system is designed to be transparent—every scoring decision can be traced through the `score_breakdown` field to understand exactly why a task received its priority.