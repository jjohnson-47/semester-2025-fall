#!/bin/bash
# Quick Setup Script for Worktree-Based Orchestration
# Save as: setup_orchestration.sh
# Usage: ./setup_orchestration.sh

set -e

echo "🚀 Setting up Worktree-Based Multiagent Orchestration System"
echo "============================================================"

# Check for dependencies
echo "📋 Checking dependencies..."

if ! command -v git &> /dev/null; then
    echo "❌ git is required but not installed"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ python3 is required but not installed"
    exit 1
fi

if ! command -v claude-code &> /dev/null; then
    echo "⚠️  claude-code CLI not found"
    echo "   Please install from: https://docs.anthropic.com/en/docs/claude-code"
    read -p "   Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "✅ Dependencies checked"

# Create required files
echo "📁 Creating orchestration files..."

# 1. Create main orchestration script
cat > worktree_orchestrate.sh <<'SCRIPT_EOF'
#!/bin/bash
# [Full worktree_orchestrate.sh content goes here - copy from the worktree-orchestrator artifact]
# This is a placeholder - replace with the full script content
echo "Please replace this with the full worktree_orchestrate.sh script from the artifacts"
SCRIPT_EOF

# 2. Create monitor script
cat > monitor_orchestration.py <<'MONITOR_EOF'
#!/usr/bin/env python3
# [Full monitor_orchestration.py content goes here - copy from the tracker-monitor artifact]
# This is a placeholder - replace with the full script content
print("Please replace this with the full monitor_orchestration.py script from the artifacts")
MONITOR_EOF

# 3. Create probe directives
cat > probe_directives.md <<'PROBES_EOF'
# Probe Directives
# [Copy the full probe directives content here from the probe-directives artifact]
# This is a placeholder - replace with the full probe directives

## Probe V2: Repository State
[V2 content here]

## Probe V3: Enrichment  
[V3 content here]
PROBES_EOF

# Make scripts executable
chmod +x worktree_orchestrate.sh
chmod +x monitor_orchestration.py

echo "✅ Files created"

# Initialize git if needed
if [ ! -d .git ]; then
    echo "📦 Initializing git repository..."
    git init
    git add .
    git commit -m "Initial commit for orchestration"
fi

# Update gitignore
echo "📝 Updating .gitignore..."
if [ ! -f .gitignore ]; then
    touch .gitignore
fi

# Add entries if not present
grep -q "^\.worktrees/" .gitignore || echo ".worktrees/" >> .gitignore
grep -q "^\.orchestration/" .gitignore || echo ".orchestration/" >> .gitignore
grep -q "^__pycache__/" .gitignore || echo "__pycache__/" >> .gitignore
grep -q "^*.pyc" .gitignore || echo "*.pyc" >> .gitignore

echo "✅ Git configuration updated"

# Initialize orchestration system
echo "🔧 Initializing orchestration system..."
./worktree_orchestrate.sh init

# Create example lanes configuration
echo "📋 Creating example lanes configuration..."
cat > example_lanes.json <<'EOF'
{
  "lanes": [
    {
      "id": "example-analysis",
      "name": "Example Analysis Lane",
      "tasks": [
        "Analyze repository structure",
        "Generate documentation",
        "Create test cases"
      ],
      "parallel": true,
      "priority": "medium"
    },
    {
      "id": "example-optimization",
      "name": "Example Optimization Lane",
      "tasks": [
        "Optimize database queries",
        "Add indexes",
        "Update caching strategy"
      ],
      "parallel": true,
      "priority": "high"
    }
  ]
}
EOF

echo "✅ Example configuration created"

# Show next steps
echo ""
echo "========================================="
echo "✨ Setup Complete!"
echo "========================================="
echo ""
echo "📚 Quick Start Guide:"
echo ""
echo "1. Run full orchestration:"
echo "   ./worktree_orchestrate.sh full"
echo ""
echo "2. Monitor progress (choose one):"
echo "   python3 monitor_orchestration.py          # Console"
echo "   python3 monitor_orchestration.py --web    # Web UI"
echo ""
echo "3. Check status:"
echo "   ./worktree_orchestrate.sh status"
echo ""
echo "4. Merge results when complete:"
echo "   ./worktree_orchestrate.sh merge"
echo ""
echo "5. Clean up worktrees:"
echo "   ./worktree_orchestrate.sh cleanup"
echo ""
echo "📁 Important Directories:"
echo "   .orchestration/     - Tracking data (not in git)"
echo "   .worktrees/        - Agent workspaces (not in git)"
echo "   docs/_generated/   - Output files"
echo ""
echo "📖 Documentation:"
echo "   See worktree_docs.md for complete documentation"
echo ""
echo "⚠️  IMPORTANT:"
echo "   Replace the placeholder content in:"
echo "   - worktree_orchestrate.sh"
echo "   - monitor_orchestration.py"
echo "   - probe_directives.md"
echo "   with the full content from the provided artifacts"
echo ""
echo "🎯 To test the system with example lanes:"
echo "   ./worktree_orchestrate.sh add-lane example-analysis '\$(cat example_lanes.json | jq .lanes[0])'"
echo "   ./worktree_orchestrate.sh exec-lane example-analysis"
echo ""
echo "Good luck with your orchestration! 🚀"
