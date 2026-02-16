---
name: autonomous-coding
description: Fully autonomous software development - from requirement to completion with no manual intervention
license: MIT
compatibility: opencode
metadata:
  author: "Autonomous Coding System"
  version: "3.0.0"
  category: "development"
  workflow: "fully-automated"
  global: true
---

# Autonomous Coding Skill - Fully Automated Mode

## Overview
This skill provides end-to-end autonomous software development. Simply describe what you want to build, and the system will automatically plan, implement, test, and deliver the complete project with no manual intervention required.

## How It Works

### 1. **Single Command Invocation**
- User provides requirement
- System handles everything automatically
- No manual task management needed

### 2. **Automatic Workflow**
- **Planning**: Automatically breaks down requirement into subtasks
- **Implementation**: Generates and implements code for each task
- **Testing**: Runs tests after each implementation
- **Refinement**: Adjusts task list based on results
- **Completion**: Delivers finished project

### 3. **Intelligent Automation**
- Context-aware coding for each task
- Automatic test execution and validation
- Smart retry mechanisms for failures
- Git integration for version control
- Progress tracking and status updates

## Usage

### Basic Invocation
```bash
# Simply describe what you want
Create a web application with React and Node.js
```

### With Options
```bash
# With custom project directory
Create a todo application --project-dir "/path/to/project"

# With specific AI model
Create a REST API --model "gemini-2.0-flash-exp"

# With recovery mode (after crash)
Create a data processing pipeline --recover
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
   - Commits successful changes
   - Handles failures and retries

3. **Completion Phase**
   - Shows final results
   - Provides project summary
   - Handles any final refinements

## Features

### 🚀 **Full Automation**
- No manual task management
- End-to-end workflow
- Intelligent error handling
- Automatic recovery

### 🎯 **Smart Planning**
- Context-aware task breakdown
- Hierarchical task organization
- Test-driven approach

### 💻 **Intelligent Implementation**
- Full file context awareness
- Smart code generation
- Error handling and retry

### 🧪 **Automated Testing**
- Test execution after each task
- Validation and verification
- Continuous integration

### 📊 **Progress Tracking**
- Real-time progress updates
- Automatic status reporting
- Completion tracking

## Global Installation

### One-Time Setup
```bash
# Install skill globally
mkdir -p ~/.config/opencode/skills/autonomous-coding
cp SKILL.md *.py requirements.txt ~/.config/opencode/skills/autonomous-coding/

# Install dependencies
pip install -r requirements.txt
```

## Examples

### Simple Web App
```bash
Create a React application with TypeScript and Tailwind CSS
```

### API Development
```bash
Build a REST API with Node.js, Express, and PostgreSQL
```

### Full Stack Application
```bash
Create a full-stack web application with React frontend and Node.js backend
```

## Benefits

### ✅ **Simplicity**
- Single command to start
- No manual intervention needed
- Clear and intuitive interface

### ✅ **Efficiency**
- End-to-end automation
- Intelligent task management
- Smart error handling

### ✅ **Reliability**
- Automatic recovery from failures
- Test-driven development
- Version control integration

### ✅ **Flexibility**
- Works with any project type
- Configurable options
- Context-aware implementation

## Troubleshooting

### Common Issues
- **Requirement unclear**: Provide more specific details
- **Tests failing**: System will automatically retry with different approaches
- **Git issues**: System will handle version control automatically

### Getting Help
- Use natural language to ask for clarification
- System will provide guidance automatically
- No manual status management needed

## Integration Notes

This skill provides a completely hands-off approach to software development:
- Describe what you want
- System handles everything else
- Get the finished result
- No manual task management required

The perfect balance between AI capability and user simplicity.