#!/bin/bash
# Worktree-Based Multiagent Orchestration System
# Save as: worktree_orchestrate.sh
# Usage: ./worktree_orchestrate.sh [command] [options]

set -e

# Configuration
MAIN_REPO=$(pwd)
WORKTREES_DIR="${MAIN_REPO}/.worktrees"
TRACKER_DIR="${MAIN_REPO}/.orchestration"
TRACKER_FILE="${TRACKER_DIR}/tracker.json"
TRACKER_LOCK="${TRACKER_DIR}/tracker.lock"
CLAUDE="claude-code"

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${GREEN}[ORCHESTRATOR]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }
print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }

# Initialize orchestration system
init_orchestration() {
    print_status "Initializing orchestration system..."
    
    # Create directories
    mkdir -p "$WORKTREES_DIR"
    mkdir -p "$TRACKER_DIR"
    
    # Initialize tracker if it doesn't exist
    if [ ! -f "$TRACKER_FILE" ]; then
        cat > "$TRACKER_FILE" <<EOF
{
  "version": "1.0.0",
  "main_repo": "$MAIN_REPO",
  "worktrees_dir": "$WORKTREES_DIR",
  "created_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "agents": {},
  "lanes": {},
  "phase": 0,
  "status": "initialized"
}
EOF
        print_status "Tracker initialized at $TRACKER_FILE"
    fi
    
    # Create gitignore for worktrees
    if ! grep -q "^\.worktrees/" .gitignore 2>/dev/null; then
        echo ".worktrees/" >> .gitignore
        echo ".orchestration/" >> .gitignore
        print_info "Added .worktrees/ and .orchestration/ to .gitignore"
    fi
}

# Atomic tracker updates with file locking
update_tracker() {
    local operation=$1
    shift
    
    # Acquire lock (with timeout)
    local timeout=30
    local elapsed=0
    while [ -f "$TRACKER_LOCK" ] && [ $elapsed -lt $timeout ]; do
        sleep 0.5
        elapsed=$((elapsed + 1))
    done
    
    if [ -f "$TRACKER_LOCK" ]; then
        print_warning "Lock timeout - forcing update"
        rm -f "$TRACKER_LOCK"
    fi
    
    # Create lock
    echo $$ > "$TRACKER_LOCK"
    
    # Perform update
    python3 - <<PYTHON
import json
import sys
from datetime import datetime

tracker_file = "$TRACKER_FILE"
operation = "$operation"
args = sys.argv[1:]

with open(tracker_file, 'r') as f:
    data = json.load(f)

data["updated_at"] = datetime.utcnow().isoformat() + "Z"

if operation == "add_agent":
    agent_id, worktree_path, lane_id = args[0], args[1], args[2]
    data["agents"][agent_id] = {
        "id": agent_id,
        "worktree": worktree_path,
        "lane": lane_id,
        "status": "created",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "pid": None
    }
    
elif operation == "update_agent_status":
    agent_id, status = args[0], args[1]
    if agent_id in data["agents"]:
        data["agents"][agent_id]["status"] = status
        data["agents"][agent_id]["status_changed_at"] = datetime.utcnow().isoformat() + "Z"
        if len(args) > 2:
            data["agents"][agent_id]["pid"] = int(args[2])
            
elif operation == "add_lane":
    lane_id = args[0]
    lane_data = json.loads(args[1])
    data["lanes"][lane_id] = {
        **lane_data,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    
elif operation == "update_lane_status":
    lane_id, status = args[0], args[1]
    if lane_id in data["lanes"]:
        data["lanes"][lane_id]["status"] = status
        data["lanes"][lane_id]["status_changed_at"] = datetime.utcnow().isoformat() + "Z"
        
elif operation == "update_phase":
    data["phase"] = int(args[0])
    data["status"] = args[1] if len(args) > 1 else "running"
    
elif operation == "add_result":
    lane_id, result_file = args[0], args[1]
    if lane_id in data["lanes"]:
        if "results" not in data["lanes"][lane_id]:
            data["lanes"][lane_id]["results"] = []
        data["lanes"][lane_id]["results"].append({
            "file": result_file,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })

with open(tracker_file, 'w') as f:
    json.dump(data, f, indent=2)

print(f"Tracker updated: {operation}")
PYTHON "$@"
    
    # Release lock
    rm -f "$TRACKER_LOCK"
}

# Create a worktree for an agent
create_worktree() {
    local agent_id=$1
    local branch_name=$2
    local base_branch=${3:-main}
    
    local worktree_path="${WORKTREES_DIR}/${agent_id}"
    
    if [ -d "$worktree_path" ]; then
        print_warning "Worktree for $agent_id already exists"
        return 0
    fi
    
    print_status "Creating worktree for agent: $agent_id"
    
    # Create branch if it doesn't exist
    if ! git rev-parse --verify "$branch_name" >/dev/null 2>&1; then
        git branch "$branch_name" "$base_branch"
    fi
    
    # Add worktree
    git worktree add -b "$branch_name" "$worktree_path" "$base_branch" 2>/dev/null || \
    git worktree add "$worktree_path" "$branch_name"
    
    print_info "Worktree created at: $worktree_path"
    return 0
}

# Remove a worktree
remove_worktree() {
    local agent_id=$1
    local worktree_path="${WORKTREES_DIR}/${agent_id}"
    
    if [ ! -d "$worktree_path" ]; then
        print_warning "Worktree for $agent_id doesn't exist"
        return 0
    fi
    
    print_status "Removing worktree for agent: $agent_id"
    git worktree remove "$worktree_path" --force 2>/dev/null || true
    
    update_tracker "update_agent_status" "$agent_id" "removed"
}

# Execute a lane in a worktree
execute_lane() {
    local lane_id=$1
    local agent_id="agent-${lane_id}"
    local branch_name="lane-${lane_id}"
    local worktree_path="${WORKTREES_DIR}/${agent_id}"
    
    # Create worktree
    create_worktree "$agent_id" "$branch_name"
    update_tracker "add_agent" "$agent_id" "$worktree_path" "$lane_id"
    
    # Get lane tasks from tracker
    local tasks=$(python3 -c "
import json
with open('$TRACKER_FILE') as f:
    data = json.load(f)
    lane = data['lanes'].get('$lane_id', {})
    tasks = lane.get('tasks', [])
    print('\\n'.join(f'- {t}' for t in tasks))
")
    
    print_status "Executing lane $lane_id in worktree $agent_id"
    print_info "Tasks:\n$tasks"
    
    # Update status
    update_tracker "update_agent_status" "$agent_id" "running" "$$"
    update_tracker "update_lane_status" "$lane_id" "running"
    
    # Execute in worktree
    cd "$worktree_path"
    
    # Copy tracker access script
    cat > access_tracker.py <<'PYTHON'
#!/usr/bin/env python3
import json
import sys
import fcntl
import time

def read_tracker(tracker_file):
    with open(tracker_file, 'r') as f:
        return json.load(f)

def update_tracker(tracker_file, updates):
    # Retry logic for lock acquisition
    for _ in range(30):
        try:
            with open(tracker_file, 'r+') as f:
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                data = json.load(f)
                data.update(updates)
                f.seek(0)
                json.dump(data, f, indent=2)
                f.truncate()
                fcntl.flock(f, fcntl.LOCK_UN)
                return True
        except BlockingIOError:
            time.sleep(0.5)
    return False

if __name__ == "__main__":
    tracker_file = sys.argv[1]
    if len(sys.argv) == 2:
        # Read mode
        print(json.dumps(read_tracker(tracker_file)))
    else:
        # Update mode
        updates = json.loads(sys.argv[2])
        success = update_tracker(tracker_file, updates)
        print("success" if success else "failed")
PYTHON
    chmod +x access_tracker.py
    
    # Run lane tasks
    $CLAUDE --dir "$worktree_path" --task "Execute the following tasks for lane $lane_id:
$tasks

Important instructions:
1. You are working in a git worktree at: $worktree_path
2. Your branch is: $branch_name
3. The main repository is at: $MAIN_REPO
4. To read the central tracker: python3 access_tracker.py '$TRACKER_FILE'
5. To update progress: python3 access_tracker.py '$TRACKER_FILE' '{\"lanes\": {\"$lane_id\": {\"progress\": \"description\"}}}'
6. Create outputs in docs/_generated/ within this worktree
7. Commit your changes to your branch when complete"
    
    local exit_code=$?
    
    # Update status based on result
    if [ $exit_code -eq 0 ]; then
        update_tracker "update_lane_status" "$lane_id" "completed"
        update_tracker "update_agent_status" "$agent_id" "completed"
        print_status "Lane $lane_id completed successfully"
        
        # Collect results
        if [ -d "docs/_generated" ]; then
            for file in docs/_generated/*; do
                if [ -f "$file" ]; then
                    update_tracker "add_result" "$lane_id" "$(basename $file)"
                fi
            done
        fi
    else
        update_tracker "update_lane_status" "$lane_id" "failed"
        update_tracker "update_agent_status" "$agent_id" "failed"
        print_error "Lane $lane_id failed with exit code $exit_code"
    fi
    
    cd "$MAIN_REPO"
    return $exit_code
}

# Run probes phase
run_probes() {
    print_status "Phase 1: Running System Probes"
    update_tracker "update_phase" "1" "running"
    
    # Define probe lanes
    update_tracker "add_lane" "probe-v2" '{
        "name": "Repository State Probe",
        "tasks": ["Execute Repository State Probe V2", "Generate state_probe.json"],
        "parallel": true
    }'
    
    update_tracker "add_lane" "probe-v3" '{
        "name": "Enrichment Probe",
        "tasks": ["Execute Enrichment Probe V3", "Generate plan_input.json"],
        "parallel": true
    }'
    
    # Execute probes in parallel
    execute_lane "probe-v2" &
    PID1=$!
    
    execute_lane "probe-v3" &
    PID2=$!
    
    # Wait for completion
    wait $PID1
    PROBE1_STATUS=$?
    wait $PID2
    PROBE2_STATUS=$?
    
    if [ $PROBE1_STATUS -eq 0 ] && [ $PROBE2_STATUS -eq 0 ]; then
        update_tracker "update_phase" "1" "completed"
        
        # Merge probe results to main
        print_status "Merging probe results to main repository"
        for agent_id in "agent-probe-v2" "agent-probe-v3"; do
            worktree_path="${WORKTREES_DIR}/${agent_id}"
            if [ -d "$worktree_path/docs/_generated" ]; then
                cp -r "$worktree_path/docs/_generated/"* "$MAIN_REPO/docs/_generated/" 2>/dev/null || true
            fi
        done
        
        print_status "Phase 1 completed successfully"
        return 0
    else
        update_tracker "update_phase" "1" "failed"
        print_error "Phase 1 failed"
        return 1
    fi
}

# Generate execution plan from probe results
generate_plan() {
    print_status "Phase 2: Generating Execution Plan"
    update_tracker "update_phase" "2" "running"
    
    if [ ! -f "docs/_generated/state_probe.json" ] || [ ! -f "docs/_generated/plan_input.json" ]; then
        print_error "Probe outputs missing. Run probes first."
        update_tracker "update_phase" "2" "failed"
        return 1
    fi
    
    python3 - <<'PYTHON'
import json
import os

# Load probe results
state = json.load(open("docs/_generated/state_probe.json"))
plan = json.load(open("docs/_generated/plan_input.json"))
tracker = json.load(open("$TRACKER_FILE"))

lanes = []

# Analyze and create lanes
if not state["db"].get("has_course_projection"):
    lanes.append({
        "id": "db-projection",
        "name": "Database Projection Tables",
        "tasks": [
            "Create course_projection table",
            "Create course_registry table", 
            "Add origin tracking columns to tasks",
            "Create indexes for projection queries"
        ],
        "parallel": True,
        "priority": "high"
    })

if not state["db"].get("has_events"):
    lanes.append({
        "id": "db-events",
        "name": "Event Tracking System",
        "tasks": [
            "Create events table",
            "Add event triggers",
            "Create event indexes"
        ],
        "parallel": True,
        "priority": "high"
    })

# Check for missing manifests
courses = state.get("courses", {}).get("courses", [])
missing_manifests = [c["course_code"] for c in courses if not c.get("has_manifest")]
if missing_manifests:
    for course in missing_manifests:
        lanes.append({
            "id": f"manifest-{course.lower()}",
            "name": f"Generate {course} Manifest",
            "tasks": [
                f"Analyze {course} JSON files",
                f"Generate course_manifest.json for {course}",
                "Validate manifest structure"
            ],
            "parallel": True,
            "priority": "medium"
        })

# Check for missing indexes
db = plan.get("db", {})
hot_indexes = db.get("hot_index_present", {})
if not all(hot_indexes.values()):
    lanes.append({
        "id": "db-indexes",
        "name": "Performance Indexes",
        "tasks": [
            f"Create index on {col}" 
            for col, present in hot_indexes.items() 
            if not present
        ],
        "parallel": True,
        "priority": "medium"
    })

# Test infrastructure
if plan.get("tests", {}).get("count", 0) == 0:
    lanes.append({
        "id": "test-setup",
        "name": "Test Infrastructure",
        "tasks": [
            "Create test fixtures",
            "Write API endpoint tests",
            "Write dashboard tests",
            "Configure pytest"
        ],
        "parallel": False,
        "priority": "low"
    })

# Save execution plan
execution_plan = {
    "phase": 3,
    "lanes": lanes,
    "total_lanes": len(lanes),
    "parallel_lanes": sum(1 for l in lanes if l.get("parallel", False)),
    "sequential_lanes": sum(1 for l in lanes if not l.get("parallel", False))
}

with open("docs/_generated/execution_plan.json", "w") as f:
    json.dump(execution_plan, f, indent=2)

# Update tracker with lanes
import sys
sys.path.insert(0, '.')
for lane in lanes:
    os.system(f"./worktree_orchestrate.sh add-lane '{lane['id']}' '{json.dumps(lane)}'")

print(f"Generated execution plan with {len(lanes)} lanes")
print(f"- Parallel: {execution_plan['parallel_lanes']}")
print(f"- Sequential: {execution_plan['sequential_lanes']}")
PYTHON
    
    if [ $? -eq 0 ]; then
        update_tracker "update_phase" "2" "completed"
        print_status "Phase 2 completed successfully"
        return 0
    else
        update_tracker "update_phase" "2" "failed"
        print_error "Phase 2 failed"
        return 1
    fi
}

# Execute work lanes
execute_lanes() {
    print_status "Phase 3: Executing Work Lanes"
    update_tracker "update_phase" "3" "running"
    
    if [ ! -f "docs/_generated/execution_plan.json" ]; then
        print_error "Execution plan missing. Generate plan first."
        update_tracker "update_phase" "3" "failed"
        return 1
    fi
    
    # Get lanes from plan
    local parallel_lanes=$(python3 -c "
import json
plan = json.load(open('docs/_generated/execution_plan.json'))
for lane in plan['lanes']:
    if lane.get('parallel', False):
        print(lane['id'])
")
    
    local sequential_lanes=$(python3 -c "
import json
plan = json.load(open('docs/_generated/execution_plan.json'))
for lane in plan['lanes']:
    if not lane.get('parallel', False):
        print(lane['id'])
")
    
    # Execute parallel lanes
    if [ -n "$parallel_lanes" ]; then
        print_status "Starting parallel lanes..."
        declare -a pids
        for lane_id in $parallel_lanes; do
            execute_lane "$lane_id" &
            pids+=($!)
        done
        
        # Wait for all parallel lanes
        for pid in "${pids[@]}"; do
            wait $pid
        done
    fi
    
    # Execute sequential lanes
    if [ -n "$sequential_lanes" ]; then
        print_status "Starting sequential lanes..."
        for lane_id in $sequential_lanes; do
            execute_lane "$lane_id"
        done
    fi
    
    update_tracker "update_phase" "3" "completed"
    print_status "Phase 3 completed"
}

# Monitor tracker changes (for orchestrator view)
monitor() {
    print_status "Monitoring orchestration progress..."
    print_info "Press Ctrl+C to stop monitoring"
    
    python3 - <<'PYTHON'
import json
import time
import os
from datetime import datetime

tracker_file = "$TRACKER_FILE"
last_update = None

while True:
    try:
        with open(tracker_file, 'r') as f:
            data = json.load(f)
        
        current_update = data.get("updated_at", "")
        
        if current_update != last_update:
            os.system("clear")
            print(f"=== ORCHESTRATION STATUS === {datetime.now().strftime('%H:%M:%S')}")
            print(f"Phase: {data.get('phase', 0)} - Status: {data.get('status', 'unknown')}")
            print(f"Last Update: {current_update}\n")
            
            # Agents status
            print("AGENTS:")
            for agent_id, agent in data.get("agents", {}).items():
                status_icon = "✓" if agent["status"] == "completed" else "✗" if agent["status"] == "failed" else "→"
                print(f"  {status_icon} {agent_id}: {agent['status']} (lane: {agent['lane']})")
            
            # Lanes status
            print("\nLANES:")
            for lane_id, lane in data.get("lanes", {}).items():
                status_icon = "✓" if lane["status"] == "completed" else "✗" if lane["status"] == "failed" else "→" if lane["status"] == "running" else "○"
                results = len(lane.get("results", []))
                print(f"  {status_icon} {lane_id}: {lane['status']} ({results} results)")
                
            last_update = current_update
        
        time.sleep(2)
        
    except KeyboardInterrupt:
        print("\nMonitoring stopped")
        break
    except Exception as e:
        print(f"Error reading tracker: {e}")
        time.sleep(5)
PYTHON
}

# Merge branches back to main
merge_results() {
    print_status "Merging results back to main branch"
    
    local branches=$(git branch -r | grep "lane-" | sed 's/origin\///')
    
    for branch in $branches; do
        print_info "Merging $branch"
        git merge "$branch" --no-ff -m "Merge $branch results" || {
            print_warning "Merge conflict in $branch - manual resolution needed"
        }
    done
    
    print_status "Merge complete"
}

# Cleanup worktrees
cleanup() {
    print_status "Cleaning up worktrees..."
    
    if [ -d "$WORKTREES_DIR" ]; then
        for worktree in "$WORKTREES_DIR"/*; do
            if [ -d "$worktree" ]; then
                agent_id=$(basename "$worktree")
                remove_worktree "$agent_id"
            fi
        done
    fi
    
    # Prune worktree list
    git worktree prune
    
    print_status "Cleanup complete"
}

# Show help
show_help() {
    cat <<EOF
Worktree-Based Multiagent Orchestration System

Usage: $0 [command] [options]

Commands:
  init          Initialize orchestration system
  probes        Run Phase 1: System probes
  plan          Run Phase 2: Generate execution plan
  execute       Run Phase 3: Execute work lanes
  monitor       Monitor orchestration progress
  merge         Merge results back to main branch
  cleanup       Remove all worktrees
  full          Run all phases sequentially
  
Lane Management:
  add-lane <id> <json>    Add a lane to the tracker
  exec-lane <id>          Execute a specific lane
  
Utility:
  status        Show current orchestration status
  reset         Reset orchestration state
  help          Show this help message

Examples:
  $0 init           # Initialize the system
  $0 full           # Run complete orchestration
  $0 monitor        # Monitor progress in another terminal
  $0 merge          # Merge all results when complete
  
Environment Variables:
  WORKTREES_DIR    Directory for worktrees (default: .worktrees)
  TRACKER_DIR      Directory for tracker (default: .orchestration)
  CLAUDE           Path to claude-code CLI (default: claude-code)
EOF
}

# Main command handler
main() {
    local command=${1:-help}
    shift || true
    
    case $command in
        init)
            init_orchestration
            ;;
        probes)
            init_orchestration
            run_probes
            ;;
        plan)
            generate_plan
            ;;
        execute)
            execute_lanes
            ;;
        monitor)
            monitor
            ;;
        merge)
            merge_results
            ;;
        cleanup)
            cleanup
            ;;
        full)
            init_orchestration
            run_probes && generate_plan && execute_lanes
            print_status "Full orchestration complete"
            print_info "Run '$0 merge' to merge results"
            ;;
        add-lane)
            local lane_id=$1
            local lane_json=$2
            update_tracker "add_lane" "$lane_id" "$lane_json"
            ;;
        exec-lane)
            local lane_id=$1
            execute_lane "$lane_id"
            ;;
        status)
            if [ -f "$TRACKER_FILE" ]; then
                cat "$TRACKER_FILE" | python3 -m json.tool
            else
                print_error "No tracker file found. Run 'init' first."
            fi
            ;;
        reset)
            print_warning "Resetting orchestration state..."
            cleanup
            rm -rf "$TRACKER_DIR"
            rm -rf "$WORKTREES_DIR"
            print_status "Reset complete"
            ;;
        help|*)
            show_help
            ;;
    esac
}

# Check for claude-code
if ! command -v $CLAUDE &> /dev/null; then
    print_error "claude-code CLI not found. Please install it first."
    print_info "Visit: https://docs.anthropic.com/en/docs/claude-code"
    exit 1
fi

# Run main
main "$@"
