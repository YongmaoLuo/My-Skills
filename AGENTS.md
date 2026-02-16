# Agent Guidelines

This repository contains Python skills for the OpenCode system: autonomous-coding and conventional-commits.

## Build/Lint/Test Commands

This is a simple Python package without standard build configuration files. No pre-commit hooks, linting, or automated testing setup exists.

### Dependency Management
```bash
pip install -r requirements.txt
```

### Running Tests
Tests are executed dynamically through the autonomous coding workflow. Each subtask defines its own test command (e.g., `pytest`, `npm test`). No single-test command exists at the repository level.

## Code Style Guidelines

### Imports
- Standard library imports first (os, json, subprocess, etc.)
- Third-party imports second (git, etc.)
- Local module imports last
- Each import group separated by a blank line

```python
import os
import re
from pathlib import Path
from typing import Optional

from coding_tool import CodingTool
from task_manager import TaskManager
```

### Formatting
- 4-space indentation (no tabs)
- Maximum line length: Not strictly enforced, but keep under 100 chars when reasonable
- Use blank lines to separate logical sections (imports, classes, functions)
- One blank line between class methods, two blank lines between top-level functions

### Types
- Use type hints for all function parameters and return values
- Import commonly used types: `Optional`, `List`, `Dict`, `Tuple`
- Use `Path` from pathlib for file paths instead of strings
- Use `Optional[T]` for nullable types

```python
def update_task_status(self, task_id: str, status: str):
def get_next_task(self) -> Optional[SubTask]:
```

### Naming Conventions
- **Classes**: PascalCase (`SubTask`, `TaskManager`, `Executor`)
- **Functions/Methods**: snake_case (`run_command`, `get_file_context`)
- **Variables**: snake_case (`project_dir`, `exit_code`)
- **Constants**: UPPER_CASE with underscores (not commonly used in this codebase)
- **Private methods**: Prefix with underscore `_internal_method()`
- **Dunder methods**: Standard Python dunder methods (`__init__`, `model_dump`)

### Docstrings
- Modules: Triple-quoted string at top describing purpose
- Classes: Docstring below class declaration
- Functions/Methods: Use Args/Returns format for complex functions

```python
"""
Task Manager
============

Manages task state, persistence, and lifecycle.
"""

class TaskManager:
    """Manages task state and persistence."""

    def __init__(self, project_dir: Path):
        pass

    def get_next_task(self) -> Optional[SubTask]:
        """
        Get the next task to process.

        Returns:
            Next task or None if all tasks are completed
        """
        pass
```

### Error Handling
- Use try/except blocks for operations that may fail (file I/O, subprocess, etc.)
- Catch specific exceptions when possible (`ValueError`, `json.JSONDecodeError`)
- Print informative error messages for debugging
- For recoverable errors, return early with default values
- For critical errors, raise exceptions with descriptive messages

```python
try:
    path_obj = path_obj.relative_to(self.project_dir)
except ValueError:
    path_obj = Path(path_obj.name)

try:
    content = f.read()
except Exception:
    pass
```

### File Operations
- Use `Path` objects from pathlib for path manipulation
- Prefer `path_obj.read_text()` and `path_obj.write_text()` over open/close
- When using open(), use context managers (`with open() as f:`)
- Create directories with `path_obj.parent.mkdir(parents=True, exist_ok=True)`
- Check file existence with `path_obj.exists()`

### String Formatting
- Use f-strings for string interpolation (Python 3.6+)
- Use f-strings for path joining: `os.path.join(root, file)`
- For multi-line strings, use triple quotes
- Keep print statements concise and informative

### JSON Handling
- Use `json.dump()` and `json.load()` for file operations
- Use `indent=2` for human-readable JSON output
- Validate JSON structure after parsing with `.get()` or try/except

```python
json.dump({"requirement": self.requirement, "tasks": tasks_data}, f, indent=2)
plan_response = self.coding_tool.query_json(...)
if "tasks" in breakdown_response:
    tasks = breakdown_response["tasks"]
```

### Git Operations
- Use GitPython library for git operations
- Import git inside methods to reduce dependencies when not used: `import git`
- Use `repo.git.add(A=True)` to stage all changes
- Use `repo.index.commit(message)` to commit staged changes
- Use `repo.git.diff(None)` to get unstaged diff
- Use `repo.untracked_files` to list untracked files

### Subprocess Execution
- Use `subprocess.Popen` for command execution with output capture
- Set `stdout=subprocess.PIPE`, `stderr=subprocess.STDOUT` for combined output
- Use `text=True` for string output instead of bytes
- Use `cwd` parameter to specify working directory
- Poll process and read output line by line

```python
process = subprocess.Popen(
    command, shell=True,
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    text=True, cwd=self.project_dir
)
```

### Task Management
- Task IDs are hierarchical strings: "1", "1-1", "1-1-1"
- Use hyphens to connect parent and child task IDs
- Status values: "pending", "in_progress", "completed", "failed"
- Timestamps use ISO 8601 format: `datetime.utcnow().isoformat()`
- Preserve metadata (status, updated_time) when updating tasks

### Conventional Commits
Follow Conventional Commits specification:
- Format: `<type>[optional scope]: <description>`
- Types: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert
- Imperative mood for subject line
- Subject under 72 characters recommended
- Body and footer optional
- Breaking changes marked with `BREAKING CHANGE:` in footer

### Code Organization
- Each skill in its own directory with SKILL.md
- Main logic in modules: agent.py, task_manager.py, executor.py, git_manager.py, refiner.py
- Data models: task.py
- Entry points: cli.py, __init__.py
- requirements.txt for dependencies
- tasks.json for task persistence (auto-generated)

### Comments
- No inline comments unless necessary for complex logic
- No block comments at end of functions
- Docstrings should be self-explanatory
- Avoid comment decorations or visual separators
