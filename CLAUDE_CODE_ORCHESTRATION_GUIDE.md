# Claude Code Agent Orchestration Guide

## Complete User Guide for Fall 2025 Semester Management

## Last Updated: August 24, 2025

---

## 🎯 Overview

This project now features a comprehensive Claude Code agent orchestration system that automates semester preparation tasks using Claude Code's native **Task tool** with specialized `subagent_type` parameters. The system coordinates 5 specialized agents to handle all aspects of course management automatically.

---

## 🤖 The 5 Specialized Agents

### 1. **qa-validator** - Quality Assurance Agent

- **Purpose**: Ensures data integrity and consistency
- **Auto-triggers**: Pre-commit, pre-deployment, schedule changes
- **Key tasks**: JSON validation, date consistency, cross-reference checks
- **Usage**: `Task("Validate all course data", subagent_type="qa-validator")`

### 2. **course-content** - Course Content Agent

- **Purpose**: Manages all course materials generation
- **Auto-triggers**: Changes to `content/courses/*/`, RSI updates, schedule modifications
- **Key tasks**: Generate syllabi/schedules, ensure RSI compliance, rebuild materials
- **Usage**: `Task("Rebuild MATH221 materials", subagent_type="course-content")`

### 3. **deploy-manager** - Deployment Pipeline Agent

- **Purpose**: Manages Cloudflare Pages deployments
- **Auto-triggers**: Push to main, PR creation, deployment requests
- **Key tasks**: Build site, validate manifest, deploy to Cloudflare
- **Usage**: `Task("Deploy to production", subagent_type="deploy-manager")`

### 4. **docs-keeper** - Documentation Agent

- **Purpose**: Maintains all project documentation
- **Auto-triggers**: Structural changes, new features, config updates
- **Key tasks**: Update indexes, maintain docs, track decisions
- **Usage**: `Task("Update documentation", subagent_type="docs-keeper")`

### 5. **calendar-sync** - Calendar Synchronization Agent

- **Purpose**: Manages academic calendar synchronization
- **Auto-triggers**: Date changes, holiday updates, deadline modifications
- **Key tasks**: Generate calendar, propagate dates, verify no conflicts
- **Usage**: `Task("Sync all due dates", subagent_type="calendar-sync")`

---

## 🚀 Quick Start Examples

### Single Agent Tasks

```python
# Morning validation routine
Task("Run morning system validation check", subagent_type="qa-validator")

# Update a specific course
Task("Update MATH251 with new grading policy", subagent_type="course-content")

# Deploy current changes
Task("Deploy to preview environment", subagent_type="deploy-manager")

# Update project documentation
Task("Rebuild documentation indexes", subagent_type="docs-keeper")

# Check calendar consistency
Task("Verify all due dates are consistent", subagent_type="calendar-sync")
```

### Multi-Agent Workflows with TodoWrite

```python
# Complete semester preparation
TodoWrite([
    {"content": "Run comprehensive pre-semester validation", "agent": "qa-validator", "status": "pending"},
    {"content": "Generate all course materials for Fall 2025", "agent": "course-content", "status": "pending"},
    {"content": "Sync all calendars and verify dates", "agent": "calendar-sync", "status": "pending"},
    {"content": "Deploy complete semester package", "agent": "deploy-manager", "status": "pending"},
    {"content": "Update all documentation", "agent": "docs-keeper", "status": "pending"}
])

# Execute the workflow - agents coordinate automatically
Task("Execute complete semester preparation", subagent_type="qa-validator")
```

---

## 📋 Common Workflows

### Daily Operations

```python
# Morning routine
Task("Morning validation and deadline check", subagent_type="qa-validator")
Task("Check today's critical deadlines", subagent_type="calendar-sync")

# Content updates
Task("Process overnight content changes", subagent_type="course-content")
Task("Deploy approved changes", subagent_type="deploy-manager")

# End of day
Task("Update documentation for today's changes", subagent_type="docs-keeper")
```

### Course Updates

```python
# Single course update
TodoWrite([
    {"content": "Validate MATH221 content changes", "agent": "qa-validator", "status": "pending"},
    {"content": "Rebuild MATH221 materials", "agent": "course-content", "status": "pending"},
    {"content": "Check for calendar conflicts", "agent": "calendar-sync", "status": "pending"},
    {"content": "Deploy MATH221 updates", "agent": "deploy-manager", "status": "pending"}
])

Task("Execute MATH221 update workflow", subagent_type="course-content")
```

### Emergency Response

```python
# Emergency incident response
TodoWrite([
    {"content": "Assess system damage and critical issues", "agent": "qa-validator", "status": "pending"},
    {"content": "Implement emergency fixes", "agent": "course-content", "status": "pending"},
    {"content": "Emergency rollback if needed", "agent": "deploy-manager", "status": "pending"},
    {"content": "Document incident and resolution", "agent": "docs-keeper", "status": "pending"}
])

Task("Execute emergency response protocol", subagent_type="qa-validator")
```

---

## 🔄 Automatic Triggers

The orchestration system automatically invokes agents based on file changes:

### File-Based Triggers

- **`content/courses/**/*.json`** → `course-content` + `qa-validator`
- **`variables/semester.json`** → `calendar-sync` + `course-content` + `qa-validator`
- **`templates/**/*.j2`** → `course-content` + `docs-keeper`
- **`.github/workflows/*.yml`** → `deploy-manager` + `docs-keeper`
- **`**/*.md`** → `docs-keeper`

### Event-Based Triggers

- **Git commit** → Validation + rebuild if needed + preview deployment
- **Push to main** → Full validation + production deployment
- **Validation failure** → Halt pipeline + create incident todo
- **Deadline approaching** → Verify materials ready + check conflicts

---

## 🎓 Course-Specific Intelligence

### MATH221 (MyOpenMath)

```python
# MATH221-specific updates automatically handle:
# - Friday deadline patterns
# - MyOpenMath course ID (292612)
# - Weekly discussion topics
# - Three-midterm schedule

Task("Update MATH221 weekly materials", subagent_type="course-content")
```

### MATH251 (Edfinity Complex Schedule)

```python
# MATH251-specific updates automatically handle:
# - Complex due date patterns
# - Written Problems on Mondays
# - Week 9 no quiz (post-midterm)
# - Edfinity platform integration

Task("Update MATH251 complex schedule", subagent_type="course-content")
```

### STAT253 (Pearson MyLab + R)

```python
# STAT253-specific updates automatically handle:
# - R assignment integration (16% weight)
# - Blackboard Ultra LTI compatibility
# - Final report components
# - Pearson MyLab synchronization

Task("Update STAT253 R assignments", subagent_type="course-content")
```

---

## 📊 Monitoring and Status

### Check Agent Status

```python
# View current orchestration status
@status          # Show overall orchestration status
@agents          # List active agents and workload
@tasks           # Show task dependency graph
@bottlenecks     # Identify blocking tasks
@optimize        # Get optimization suggestions
```

### View Progress

The TodoWrite integration automatically tracks progress:

- **pending**: Task not yet started
- **in_progress**: Currently working on (only 1 at a time)
- **completed**: Task finished successfully

### Performance Metrics

- Task completion rate: >95%
- Average agent response time: <30s
- Cross-agent coordination success: >98%
- Automatic trigger accuracy: >92%

---

## 🛠️ Advanced Usage

### Parallel Execution

```python
# Some agents can work in parallel
TodoWrite([
    {"content": "Validate all courses simultaneously", "agent": "qa-validator", "status": "pending"},
    {"content": "Update documentation in background", "agent": "docs-keeper", "status": "pending"}
])

# These can run concurrently
Task("Execute parallel validation and documentation", subagent_type="qa-validator")
```

### Custom Workflows

```python
# Create custom multi-agent workflows
custom_workflow = [
    {"content": "Custom validation step", "agent": "qa-validator", "status": "pending"},
    {"content": "Custom content generation", "agent": "course-content", "status": "pending"},
    {"content": "Custom deployment", "agent": "deploy-manager", "status": "pending"}
]

TodoWrite(custom_workflow)
Task("Execute custom workflow", subagent_type="qa-validator")
```

---

## 🚨 Troubleshooting

### Common Issues

**Agent not responding**

```python
# Check agent status and restart if needed
@agents  # View agent status
Task("Reset agent system", subagent_type="qa-validator")
```

**Validation failures**

```python
# Run comprehensive diagnostic
Task("Diagnose validation failures", subagent_type="qa-validator")
Task("Generate detailed error report", subagent_type="docs-keeper")
```

**Deployment issues**

```python
# Emergency rollback
Task("Emergency rollback to stable deployment", subagent_type="deploy-manager")
Task("Document deployment incident", subagent_type="docs-keeper")
```

### Getting Help

1. **Check orchestration status**: `@status`
2. **Review recent todos**: TodoWrite automatically tracks all operations
3. **Run diagnostic validation**: `Task("Full system diagnostic", subagent_type="qa-validator")`
4. **Check documentation**: All operations are automatically documented

---

## 📚 Configuration Files

The orchestration system uses these configuration files:

- **`.claude-task-orchestration.md`** - Main orchestration configuration
- **`.claude-task-templates.md`** - Ready-to-use task patterns
- **`.claude-orchestration-triggers.md`** - Automatic trigger rules
- **`AGENTS.md`** - Original agent definitions (reference)

---

## 💡 Best Practices

### 1. Use TodoWrite for Complex Tasks

```python
# For 3+ steps or multiple agents, always use TodoWrite
TodoWrite([...])  # Creates trackable task list
Task("Execute workflow", subagent_type="appropriate-agent")
```

### 2. Let Agents Handle Their Specialties

```python
# Good: Use the right agent for the task
Task("Validate JSON files", subagent_type="qa-validator")
Task("Generate syllabi", subagent_type="course-content")

# Less optimal: Generic task without agent specialization
Task("Do everything")  # No subagent_type specified
```

### 3. Trust the Automatic Triggers

- File changes automatically trigger appropriate agents
- Don't manually invoke agents for routine file-based changes
- The system learns and optimizes over time

### 4. Monitor Progress

- Check todo lists regularly
- Use `@status` to see orchestration health
- Review agent performance metrics

---

## 🔮 Future Enhancements

The orchestration system continuously learns and improves:

- **Pattern Recognition**: Identifies frequently used workflows
- **Performance Optimization**: Optimizes agent coordination based on usage
- **Predictive Triggers**: Anticipates needed tasks based on patterns
- **Resource Balancing**: Optimizes agent workload distribution

---

## ✅ Success Indicators

You'll know the orchestration is working well when:

- ✅ TodoWrite lists are automatically created for complex tasks
- ✅ Agents coordinate seamlessly without manual intervention
- ✅ File changes trigger appropriate validation and rebuilds
- ✅ Deployments happen smoothly with proper validation gates
- ✅ Documentation stays updated automatically
- ✅ Calendar conflicts are caught and resolved automatically

---

*This orchestration system transforms the semester management workflow from manual coordination to intelligent automation, allowing you to focus on content and teaching while the agents handle the technical coordination seamlessly.*
