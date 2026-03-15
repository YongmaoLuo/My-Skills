---
name: autonomous-coding
description: Fully autonomous software development - from requirement to completion with no manual intervention
license: MIT
compatibility: opencode
metadata:
  author: "Autonomous Coding System"
  version: "4.0.0"
  category: "development"
  workflow: "fully-automated"
  global: true
---

# Autonomous Coding Skill v4.0

## Overview
This skill provides end-to-end autonomous software development. Simply describe what you want to build, and the system will automatically plan, implement, test, and deliver the complete project with no manual intervention required.

## What's New in v4.0

### Domain-Specific Configurations
- Use `--config coding` for general software development (default)
- Use `--config harmonyos` for HarmonyOS app development
- Create custom configs in `configs/` directory as YAML files

### Smart Retry Mechanism
- Automatic retry with error context (up to 5 attempts)
- Intelligent task breakdown on repeated failures
- Progress tracking across retry attempts

### Background Process Management
- Long-running commands run as background processes
- Auto-detection of stuck processes (no output for 3 minutes)
- Auto-detection of timeout (exceeds 30 minutes)

### Rollback Mechanism
- Each successful task creates a git commit checkpoint
- Easy rollback to any previous task state
- View rollback points: `autonomous-coding rollback list -w ./project`
- Rollback to task: `autonomous-coding rollback to 1-2 -w ./project`
- Rollback to previous: `autonomous-coding rollback prev -w ./project`

## Usage

### Basic Invocation
```bash
# General software development
autonomous-coding "Create a REST API with FastAPI" -w ./myproject

# HarmonyOS development
autonomous-coding --config harmonyos "Create a login page" -w ./harmonyos-app
```

### With Options
```bash
# With custom project directory
autonomous-coding "Create a todo app" -w ./todo-app

# With max tasks limit
autonomous-coding "Build a web scraper" -w ./scraper --max-tasks 10

# Recovery mode (after crash)
autonomous-coding --recover -w ./myproject
```

### Rollback Commands
```bash
# List available rollback points
autonomous-coding rollback list -w ./myproject

# Rollback to specific task
autonomous-coding rollback to 1-2 -w ./myproject

# Rollback to previous task (keeps changes stashed)
autonomous-coding rollback prev --keep -w ./myproject
```

### List Configurations
```bash
autonomous-coding configs
```

## What Happens Automatically

1. **Planning Phase**
   - Analyzes requirement
   - Breaks down into testable subtasks
   - Saves to tasks.json

2. **Execution Phase**
   - Processes each task automatically
   - Generates code with full context
   - Runs tests after each implementation
   - Commits successful changes with task checkpoint format
   - Handles failures with smart retry

3. **Completion Phase**
   - Shows final results
   - Provides project summary
   - All successful tasks have rollback points

## Features

### Full Automation
- No manual task management
- End-to-end workflow
- Intelligent error handling
- Automatic recovery

### Smart Planning
- Context-aware task breakdown
- Hierarchical task organization (1, 1-1, 1-1-1)
- Test-driven approach

### Intelligent Implementation
- Full file context awareness
- Smart code generation
- Error handling with retry (up to 5 times)
- Task breakdown on repeated failures

### Automated Testing
- Test execution after each task
- Validation and verification
- Continuous integration

### Rollback Support
- Git checkpoint for each successful task
- Easy rollback via CLI
- Stash or discard changes option

### Background Execution
- Long commands run as background processes
- Auto-detection of stuck/timeout processes
- Graceful process termination

## Configuration

### Built-in Configurations
- `coding` - General software development (default)
- `harmonyos` - HarmonyOS application development

### Custom Configuration
Create a YAML file in `configs/` directory:
```yaml
name: my-custom-config
domain_knowledge: |
  Your domain-specific knowledge here
planner_system_prompt: |
  Your planner prompt here
executor_system_prompt: |
  Your executor prompt here
file_patterns:
  - "*.py"
  - "*.js"
max_retries: 5
background_task_timeout: 180
```

## Installation

```bash
# Install dependencies
pip install GitPython PyYAML
```

## Examples

### Simple Web App
```bash
autonomous-coding "Create a React application with TypeScript and Tailwind CSS" -w ./react-app
```

### API Development
```bash
autonomous-coding "Build a REST API with Node.js, Express, and PostgreSQL" -w ./api
```

### HarmonyOS Development
```bash
autonomous-coding --config harmonyos "Create a login page with form validation" -w ./harmonyos-app
```

## Benefits

### Simplicity
- Single command to start
- No manual intervention needed
- Clear and intuitive interface

### Efficiency
- End-to-end automation
- Intelligent task management
- Smart error handling with retry

### Reliability
- Automatic recovery from failures
- Test-driven development
- Version control integration with checkpoints

### Flexibility
- Works with any project type
- Configurable options for different domains
- Context-aware implementation

## Troubleshooting

- **Requirement unclear**: Provide more specific details
- **Tests failing**: System will automatically retry with different approaches (up to 5 times)
- **Git issues**: System will handle version control automatically
- **Want to undo changes**: Use `autonomous-coding rollback` commands
- **Long-running commands**: System automatically handles background processes

## File Structure

```
autonomous-coding/
├── SKILL.md                    # This file
├── __init__.py                 # Package init
├── agent.py                    # Main orchestrator
├── background_manager.py       # Background process management
├── cli.py                      # Command line interface
├── coding_tool.py              # AI coding tool interface
├── config.py                   # AgentConfig dataclass
├── config_loader.py            # YAML config loader
├── config_registry.py          # Config registry with defaults
├── executor.py                 # Command executor
├── git_manager.py              # Git operations
├── refiner.py                  # Task list refinement
├── retry_manager.py            # Retry logic
├── rollback_manager.py         # Rollback operations
├── task.py                     # SubTask model
├── task_manager.py             # Task persistence
├── requirements.txt            # Dependencies
└── configs/
    ├── coding.yaml             # Default coding config
    └── harmonyos.yaml          # HarmonyOS-specific config
```
