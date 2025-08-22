#!/bin/bash
# Hook that runs when a dashboard task is marked complete
# Updates related files and triggers rebuilds as needed

TASK_ID="$1"
TASK_TYPE="$2"
COURSE="$3"

echo "✅ Task completed: ${TASK_TYPE} for ${COURSE}"

case "$TASK_TYPE" in
    "syllabus")
        echo "🔄 Rebuilding syllabus for ${COURSE}..."
        make course COURSE="${COURSE}" 2>/dev/null || true
        ;;
    "schedule")
        echo "🔄 Regenerating schedule..."
        make schedules 2>/dev/null || true
        ;;
    "blackboard")
        echo "📦 Updating Blackboard package..."
        uv run python scripts/build_bb_packages.py --course "${COURSE}" 2>/dev/null || true
        ;;
    "weekly")
        echo "📅 Refreshing weekly content..."
        make weekly 2>/dev/null || true
        ;;
    *)
        echo "ℹ️  No automated action for task type: ${TASK_TYPE}"
        ;;
esac

# Log completion
echo "$(date '+%Y-%m-%d %H:%M:%S') - Completed: ${TASK_TYPE} for ${COURSE}" >> .claude/task-log.txt