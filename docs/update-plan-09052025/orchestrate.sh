#!/bin/bash
# Claude Code CLI Orchestration Runner
# Save this as: orchestrate.sh
# Usage: ./orchestrate.sh [phase]

set -e

CLAUDE="claude-code"
PROBE_DOCS="probe_directives.md"
ORCHESTRATION_PLAN="orchestration_plan.md"

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[ORCHESTRATOR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to update orchestration status
update_status() {
    local phase=$1
    local lane=$2
    local status=$3
    
    python3 - <<EOF
import json
from datetime import datetime
import os

status_file = "docs/_generated/orchestration_status.json"
os.makedirs("docs/_generated", exist_ok=True)

try:
    with open(status_file, 'r') as f:
        data = json.load(f)
except:
    data = {
        "phase": 1,
        "lanes_complete": [],
        "lanes_active": [],
        "lanes_blocked": [],
        "timestamp": ""
    }

data["phase"] = $phase
data["timestamp"] = datetime.now().isoformat()

if "$status" == "complete":
    if "$lane" not in data["lanes_complete"]:
        data["lanes_complete"].append("$lane")
    if "$lane" in data["lanes_active"]:
        data["lanes_active"].remove("$lane")
elif "$status" == "active":
    if "$lane" not in data["lanes_active"]:
        data["lanes_active"].append("$lane")
elif "$status" == "blocked":
    if "$lane" not in data["lanes_blocked"]:
        data["lanes_blocked"].append("$lane")

with open(status_file, 'w') as f:
    json.dump(data, f, indent=2)

print(f"Status updated: Phase {data['phase']}, Active: {len(data['lanes_active'])}, Complete: {len(data['lanes_complete'])}")
EOF
}

# Main execution phases
run_phase_1() {
    print_status "Starting Phase 1: System State Analysis"
    
    # Run probes in parallel
    print_status "Executing Repository State Probe (V2)..."
    update_status 1 "probe-v2" "active"
    $CLAUDE --task "Execute the complete Probe V2 script from probe_directives.md. Create all outputs in docs/_generated/." &
    PID1=$!
    
    print_status "Executing Enrichment Probe (V3)..."
    update_status 1 "probe-v3" "active"
    $CLAUDE --task "Execute the complete Probe V3 script from probe_directives.md. Create all outputs in docs/_generated/." &
    PID2=$!
    
    # Wait for both probes to complete
    wait $PID1
    PROBE1_STATUS=$?
    wait $PID2
    PROBE2_STATUS=$?
    
    if [ $PROBE1_STATUS -eq 0 ]; then
        update_status 1 "probe-v2" "complete"
        print_status "Probe V2 completed successfully"
    else
        update_status 1 "probe-v2" "blocked"
        print_error "Probe V2 failed with status $PROBE1_STATUS"
    fi
    
    if [ $PROBE2_STATUS -eq 0 ]; then
        update_status 1 "probe-v3" "complete"
        print_status "Probe V3 completed successfully"
    else
        update_status 1 "probe-v3" "blocked"
        print_error "Probe V3 failed with status $PROBE2_STATUS"
    fi
    
    # Verify outputs
    if [ -f "docs/_generated/state_probe.json" ] && [ -f "docs/_generated/plan_input.json" ]; then
        print_status "Phase 1 complete: System state captured"
        return 0
    else
        print_error "Phase 1 failed: Missing probe outputs"
        return 1
    fi
}

run_phase_2() {
    print_status "Starting Phase 2: Planning Matrix Generation"
    
    # Check prerequisites
    if [ ! -f "docs/_generated/state_probe.json" ] || [ ! -f "docs/_generated/plan_input.json" ]; then
        print_error "Phase 1 outputs missing. Run phase 1 first."
        return 1
    fi
    
    update_status 2 "planning-matrix" "active"
    
    # Generate orchestration matrix
    $CLAUDE --task "Using the probe outputs in docs/_generated/, generate an orchestration matrix that identifies all work lanes and their dependencies. Create docs/_generated/orchestration_matrix.json with parallel execution lanes."
    
    if [ $? -eq 0 ]; then
        update_status 2 "planning-matrix" "complete"
        print_status "Phase 2 complete: Planning matrix generated"
        return 0
    else
        update_status 2 "planning-matrix" "blocked"
        print_error "Phase 2 failed: Could not generate planning matrix"
        return 1
    fi
}

run_phase_3() {
    print_status "Starting Phase 3: Parallel Execution Lanes"
    
    # Check prerequisites
    if [ ! -f "docs/_generated/orchestration_matrix.json" ]; then
        print_error "Phase 2 outputs missing. Run phase 2 first."
        return 1
    fi
    
    # Parse lanes from matrix and execute
    python3 - <<'PYTHON'
import json
import subprocess
import os

matrix_file = "docs/_generated/orchestration_matrix.json"
with open(matrix_file, 'r') as f:
    matrix = json.load(f)

lanes = matrix.get("lanes", [])
parallel_lanes = [l for l in lanes if l.get("parallel", False)]
sequential_lanes = [l for l in lanes if not l.get("parallel", False)]

print(f"Found {len(parallel_lanes)} parallel lanes and {len(sequential_lanes)} sequential lanes")

# Execute parallel lanes
processes = []
for lane in parallel_lanes:
    lane_id = lane["id"]
    print(f"Starting parallel lane: {lane_id}")
    
    # Create task description
    tasks = "\n".join(f"- {t}" for t in lane.get("tasks", []))
    task_desc = f"Execute lane {lane_id}:\n{tasks}\n\nWork in the repository and commit changes."
    
    # Start subprocess
    proc = subprocess.Popen([
        "claude-code", 
        "--task", 
        task_desc
    ])
    processes.append((proc, lane_id))

# Wait for all parallel processes
for proc, lane_id in processes:
    proc.wait()
    if proc.returncode == 0:
        print(f"Lane {lane_id} completed successfully")
    else:
        print(f"Lane {lane_id} failed with status {proc.returncode}")

# Execute sequential lanes
for lane in sequential_lanes:
    lane_id = lane["id"]
    print(f"Starting sequential lane: {lane_id}")
    
    tasks = "\n".join(f"- {t}" for t in lane.get("tasks", []))
    task_desc = f"Execute lane {lane_id}:\n{tasks}\n\nWork in the repository and commit changes."
    
    result = subprocess.run([
        "claude-code",
        "--task",
        task_desc
    ])
    
    if result.returncode == 0:
        print(f"Lane {lane_id} completed successfully")
    else:
        print(f"Lane {lane_id} failed with status {result.returncode}")
PYTHON
    
    if [ $? -eq 0 ]; then
        update_status 3 "execution-lanes" "complete"
        print_status "Phase 3 complete: All lanes executed"
        return 0
    else
        update_status 3 "execution-lanes" "blocked"
        print_warning "Phase 3 completed with some failures"
        return 1
    fi
}

run_validation() {
    print_status "Running final validation..."
    
    $CLAUDE --task "Validate the completed orchestration work. Check that:
    1. All course manifests exist if they were missing
    2. Database schema has been updated with new tables/columns
    3. Tests are discoverable and runnable
    4. API endpoints are documented
    5. Deploy script validates without errors
    
    Create a final report at docs/_generated/orchestration_report.md"
    
    if [ $? -eq 0 ]; then
        print_status "Validation complete. Check docs/_generated/orchestration_report.md"
        return 0
    else
        print_error "Validation failed"
        return 1
    fi
}

# Main execution
main() {
    local phase=${1:-all}
    
    print_status "Claude Code Orchestration Runner"
    print_status "Repository: $(pwd)"
    print_status "Phase: $phase"
    
    case $phase in
        1)
            run_phase_1
            ;;
        2)
            run_phase_2
            ;;
        3)
            run_phase_3
            ;;
        validate)
            run_validation
            ;;
        all)
            run_phase_1 && \
            run_phase_2 && \
            run_phase_3 && \
            run_validation
            ;;
        *)
            print_error "Unknown phase: $phase"
            echo "Usage: $0 [1|2|3|validate|all]"
            echo "  1        - Run system state analysis probes"
            echo "  2        - Generate planning matrix"
            echo "  3        - Execute parallel work lanes"
            echo "  validate - Run final validation"
            echo "  all      - Run all phases sequentially (default)"
            exit 1
            ;;
    esac
    
    # Final status report
    if [ -f "docs/_generated/orchestration_status.json" ]; then
        print_status "Final Status:"
        cat docs/_generated/orchestration_status.json | python3 -m json.tool
    fi
}

# Ensure claude-code is available
if ! command -v claude-code &> /dev/null; then
    print_error "claude-code CLI not found. Please install it first."
    exit 1
fi

# Create required directories
mkdir -p docs/_generated

# Run main orchestration
main "$@"
