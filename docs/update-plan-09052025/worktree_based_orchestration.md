# Worktree-Based Multiagent Orchestration System

## Overview

This system solves the critical problem of multiple Claude agents interfering with each other's git branches by using **git worktrees** - separate working directories that allow each agent to work in isolation while maintaining a single, centralized tracking system.

## Key Architecture Components

### 1. Git Worktrees
- Each agent gets its own isolated working directory
- Agents can switch branches without affecting others
- All worktrees share the same git repository but have independent working states

### 2. Centralized Tracker
- Single JSON file at `.orchestration/tracker.json`
- Atomic updates with file locking to prevent corruption
- All agents read/write to the same tracker
- Real-time monitoring without interfering with agent work

### 3. Branch Strategy
```
main (orchestrator)
├── lane-probe-v2 (agent worktree)
├── lane-probe-v3 (agent worktree)
├── lane-db-projection (agent worktree)
├── lane-manifest-math221 (agent worktree)
└── lane-test-setup (agent worktree)
```

## Quick Start

### Installation
```bash
# 1. Save the three artifacts to your repository
chmod +x worktree_orchestrate.sh
chmod +x monitor_orchestration.py

# 2. Initialize the system
./worktree_orchestrate.sh init

# 3. Run full orchestration
./worktree_orchestrate.sh full

# 4. In another terminal, monitor progress
python3 monitor_orchestration.py
# Or for web interface:
python3 monitor_orchestration.py --web
```

## How It Works

### Phase 1: System Probes (Parallel)
```bash
./worktree_orchestrate.sh probes
```
- Creates worktrees for probe agents
- Each probe runs in isolation on its own branch
- Results are written to `docs/_generated/` in each worktree
- Main orchestrator merges results after completion

### Phase 2: Planning
```bash
./worktree_orchestrate.sh plan
```
- Analyzes probe results from main repository
- Generates execution lanes based on gaps found
- Updates tracker with lane definitions
- Creates execution plan at `docs/_generated/execution_plan.json`

### Phase 3: Execution (Parallel/Sequential)
```bash
./worktree_orchestrate.sh execute
```
- Creates worktree for each lane
- Parallel lanes run simultaneously
- Sequential lanes wait for dependencies
- Each agent commits to its own branch

### Phase 4: Merge Results
```bash
./worktree_orchestrate.sh merge
```
- Merges all lane branches back to main
- Handles merge conflicts gracefully
- Preserves complete history

## Centralized Tracking System

### Tracker Structure
```json
{
  "version": "1.0.0",
  "phase": 3,
  "status": "running",
  "agents": {
    "agent-probe-v2": {
      "worktree": ".worktrees/agent-probe-v2",
      "lane": "probe-v2",
      "status": "completed",
      "branch": "lane-probe-v2"
    }
  },
  "lanes": {
    "probe-v2": {
      "status": "completed",
      "tasks": ["Execute probe V2"],
      "results": ["state_probe.json", "state_probe.md"],
      "priority": "high",
      "parallel": true
    }
  }
}
```

### Accessing the Tracker from Agents

Each worktree gets an `access_tracker.py` script that provides safe, locked access:

```python
# Read tracker
import json
import subprocess
result = subprocess.run(['python3', 'access_tracker.py', '/path/to/tracker.json'], 
                       capture_output=True, text=True)
data = json.loads(result.stdout)

# Update tracker
updates = {"lanes": {"my-lane": {"progress": "50% complete"}}}
subprocess.run(['python3', 'access_tracker.py', '/path/to/tracker.json', 
                json.dumps(updates)])
```

## Monitoring

### Console Monitor
```bash
python3 monitor_orchestration.py
```

Shows real-time:
- Phase progress
- Agent status (✓ completed, ✗ failed, → running, ○ created)
- Lane status with priority and results
- Overall completion percentage
- Statistics and warnings

### Web Monitor
```bash
python3 monitor_orchestration.py --web
# Open http://localhost:5555
```

Provides:
- Auto-refreshing dashboard
- Visual progress bars
- Statistics grid
- API endpoint at `/api/status`

## Example Workflow

### 1. Initialize and Start Full Orchestration
```bash
# Terminal 1 - Main orchestrator
./worktree_orchestrate.sh init
./worktree_orchestrate.sh full
```

### 2. Monitor Progress
```bash
# Terminal 2 - Monitor
python3 monitor_orchestration.py
```

### 3. Check Individual Lane Status
```bash
# Check what's happening in a specific worktree
cd .worktrees/agent-db-projection
git status
git log --oneline
```

### 4. Merge Results When Complete
```bash
./worktree_orchestrate.sh merge
```

### 5. Clean Up
```bash
./worktree_orchestrate.sh cleanup
```

## Commands Reference

### Main Commands
| Command | Description |
|---------|-------------|
| `init` | Initialize orchestration system |
| `probes` | Run system analysis probes |
| `plan` | Generate execution plan |
| `execute` | Execute work lanes |
| `monitor` | Monitor progress |
| `merge` | Merge results to main |
| `cleanup` | Remove all worktrees |
| `full` | Run complete orchestration |

### Utility Commands
| Command | Description |
|---------|-------------|
| `status` | Show current tracker state |
| `reset` | Reset entire system |
| `add-lane <id> <json>` | Manually add a lane |
| `exec-lane <id>` | Execute specific lane |

## Directory Structure

```
your-repo/
├── .orchestration/           # Centralized tracking (not in git)
│   ├── tracker.json         # Single source of truth
│   └── tracker.lock         # Lock file for atomic updates
├── .worktrees/              # Agent worktrees (not in git)
│   ├── agent-probe-v2/      # Isolated workspace
│   ├── agent-probe-v3/      # Isolated workspace
│   └── agent-db-projection/ # Isolated workspace
├── docs/_generated/         # Probe and lane outputs
├── worktree_orchestrate.sh  # Main orchestration script
└── monitor_orchestration.py # Monitoring tool
```

## Benefits

### 1. **Complete Isolation**
- Agents never interfere with each other
- Branch switching is independent per agent
- No git conflicts during parallel execution

### 2. **Centralized Tracking**
- Single tracker file prevents version conflicts
- Atomic updates with locking
- Real-time monitoring without interference

### 3. **Scalability**
- Run as many parallel agents as needed
- Each gets its own CPU/memory resources
- Easy to add more lanes dynamically

### 4. **Fault Tolerance**
- Failed agents don't affect others
- Easy to retry individual lanes
- Complete audit trail in tracker

### 5. **Clean Integration**
- All work eventually merges to main
- Preserve complete git history
- Easy rollback if needed

## Troubleshooting

### Issue: "Lock timeout - forcing update"
**Solution**: A previous operation didn't release the lock properly. The system auto-recovers.

### Issue: Worktree already exists
**Solution**: Run `./worktree_orchestrate.sh cleanup` to remove old worktrees.

### Issue: Merge conflicts
**Solution**: The system identifies conflicts but doesn't auto-resolve. Manually resolve with:
```bash
git status
git merge --continue
```

### Issue: Agent can't find tracker
**Solution**: Ensure agents use absolute paths to tracker file, provided in their task instructions.

## Advanced Usage

### Custom Lane Execution
```bash
# Define a custom lane
cat > lane.json <<EOF
{
  "name": "Custom Analysis",
  "tasks": ["Analyze performance", "Generate report"],
  "parallel": true,
  "priority": "high"
}
EOF

# Add and execute
./worktree_orchestrate.sh add-lane custom-analysis "$(cat lane.json)"
./worktree_orchestrate.sh exec-lane custom-analysis
```

### Parallel Monitoring
```bash
# Terminal 1: Console monitor
python3 monitor_orchestration.py

# Terminal 2: Web monitor
python3 monitor_orchestration.py --web

# Terminal 3: Watch tracker file directly
watch -n 1 'jq .lanes .orchestration/tracker.json'
```

### Integration with CI/CD
```yaml
# GitHub Actions example
- name: Run Orchestration
  run: |
    ./worktree_orchestrate.sh init
    ./worktree_orchestrate.sh probes
    ./worktree_orchestrate.sh plan
    ./worktree_orchestrate.sh execute
    ./worktree_orchestrate.sh merge
```

## Summary

This worktree-based system provides complete isolation for multiagent orchestration while maintaining centralized tracking. Each agent works independently without branch conflicts, and the orchestrator maintains full visibility through the single tracker file. The system is fault-tolerant, scalable, and integrates cleanly with existing git workflows.
