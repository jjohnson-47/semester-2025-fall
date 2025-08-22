# Claude Code Configuration for Fall 2025 Semester

This directory contains Claude Code configuration optimized for the KPC Fall 2025 semester management system.

## Configuration Files

### Core Configuration
- **`settings.json`** - Main project settings including permissions, hooks, and environment
- **`CLAUDE.md`** - Comprehensive project context and memory for Claude
- **`.mcp.json`** - MCP server configurations for enhanced capabilities
- **`workflows.json`** - Automated workflow definitions

### Automation
- **`hooks/`** - Shell scripts triggered by Claude Code events
  - `pre-commit.sh` - Validation before commits
  - `task-complete.sh` - Actions when dashboard tasks complete
- **`snippets.json`** - Code snippets and templates

## Key Features

### 1. Smart Permissions
The configuration implements granular permissions:
- ✅ **Allowed**: UV, Make, Git, Python scripts, content editing
- ❌ **Denied**: Dangerous operations, lock file edits, git internals
- ❓ **Ask**: GitHub operations, package installs, PDF generation

### 2. Automated Hooks
Hooks provide automation at key points:
- JSON validation on write
- Schedule rebuild on content change
- Session initialization with dependency sync
- Progress indicators for user prompts

### 3. Model Routing
Intelligent model selection based on task:
- **Sonnet** (default): Standard development tasks
- **Opus**: Architecture and complex planning
- **Haiku**: Quick edits and simple operations

### 4. MCP Servers
Enhanced capabilities through MCP:
- **GitHub**: Repository and issue management
- **Filesystem**: Safe file operations
- **Memory Bank**: Persistent cross-session memory
- **Sequential Thinking**: Structured problem-solving
- **Search**: Documentation and web research

### 5. Workflows
Pre-defined workflows for common tasks:
- `daily-start`: Morning setup routine
- `build-course COURSE=MATH221`: Build specific course
- `dashboard-start`: Launch dashboard with tasks
- `full-rebuild`: Complete system rebuild
- `semester-snapshot`: Git snapshot of state

## Usage

### Quick Start
```bash
# Claude will automatically load this configuration
claude

# Or specify a workflow
claude --workflow daily-start
```

### Running Workflows
```bash
# Use workflow aliases
claude run ds          # daily-start
claude run bc MATH221  # build-course
claude run dash        # dashboard-start
```

### Manual Hook Execution
```bash
# Run validation hook
.claude/hooks/pre-commit.sh

# Simulate task completion
.claude/hooks/task-complete.sh "task-001" "syllabus" "MATH221"
```

## Environment Variables

The configuration expects these variables (set in `.env` or shell):
- `SEMESTER`: Current semester (default: fall-2025)
- `INSTITUTION`: School name
- `BUILD_DIR`: Output directory
- `DASHBOARD_PORT`: Flask server port
- `GITHUB_TOKEN`: For GitHub MCP server (optional)
- `BRAVE_SEARCH_API_KEY`: For web search (optional)

## Best Practices

### 1. Memory Management
- CLAUDE.md is loaded automatically
- Keep it updated with major changes
- Use clear headings for easy navigation

### 2. Hook Safety
- Hooks run with limited permissions
- Always include error handling
- Use `|| true` to prevent cascade failures

### 3. Workflow Design
- Keep workflows focused and atomic
- Use parameters for flexibility
- Chain workflows for complex operations

### 4. MCP Usage
- Start only needed servers
- Configure API keys securely
- Use shortcuts for common servers

## Troubleshooting

### Configuration Not Loading
```bash
# Verify configuration
claude config validate

# Check file permissions
ls -la .claude/

# Test settings manually
claude --settings .claude/settings.json
```

### Hooks Not Running
```bash
# Check executable permissions
chmod +x .claude/hooks/*.sh

# Test hook directly
bash .claude/hooks/pre-commit.sh

# Enable verbose mode
claude --verbose
```

### MCP Server Issues
```bash
# List available servers
claude mcp list

# Test server connection
claude mcp test github

# Check server logs
claude mcp logs filesystem
```

## Advanced Features

### Custom Model Routing
Add to settings.json:
```json
"modelRouting": {
  "patterns": {
    "*/templates/*": "claude-opus-4-1-20250805",
    "*.md": "claude-haiku-4-20250514"
  }
}
```

### Dynamic Workflows
Create conditional workflows:
```json
"workflows": {
  "smart-build": {
    "condition": "git diff --name-only | grep -q content/",
    "steps": ["make validate", "make all"]
  }
}
```

### Session Persistence
Enable memory bank for context:
```bash
# Initialize memory bank
claude mcp start memory-bank

# Save session
claude session save fall-2025-work

# Restore session
claude session load fall-2025-work
```

## Security Notes

1. **Never commit** `.claude/settings.local.json` (contains secrets)
2. **Review hooks** before enabling - they execute automatically
3. **Validate permissions** - deny takes precedence over allow
4. **Rotate tokens** - Update API keys regularly
5. **Audit logs** - Check `.claude/task-log.txt` for activity

## Version History

- **1.0.0** (Aug 21, 2025) - Initial configuration with UV support
- Comprehensive hooks and workflows
- MCP server integration
- Smart model routing

---

*Configuration optimized for Claude Code August 2025 features*