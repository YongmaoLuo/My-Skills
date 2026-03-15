# Autonomous-Coding Skill Improvement Plan v2

## Executive Summary

This plan transforms the autonomous-coding skill from a coding-only tool into a **general-purpose autonomous agent framework** that can be extended with domain-specific knowledge for different task types (coding, HarmonyOS development, data processing, etc.).

### Core Principles
1. **Atomic Commits**: Each task commit creates a rollback point
2. **Fail-Safe Recovery**: Easy rollback to any task checkpoint
3. **Domain Extensibility**: Inject task-specific knowledge via configs
4. **Resilient Execution**: Smart retry + background process handling

---

## Current State Analysis

### Existing Components
| Component | File | Current Function |
|-----------|------|------------------|
| Task Model | `task.py` | Simple SubTask dataclass with id, title, description, test_command, status |
| Task Manager | `task_manager.py` | CRUD operations, persistence to tasks.json |
| Executor | `executor.py` | Blocking shell command execution |
| Coding Tool | `coding_tool.py` | AI query interface with timeout |
| Agent | `agent.py` | Main orchestrator with hardcoded coding prompts |
| Refiner | `refiner.py` | Task list refinement based on execution results |

### Current Limitations
1. **Hardcoded Planner** - Only understands coding tasks, cannot incorporate domain knowledge
2. **No Retry Logic** - Failed tasks are only broken down, not retried with different approaches
3. **Blocking Execution** - Long-running commands timeout without proper handling
4. **No Domain Extension** - Cannot inject HarmonyOS-specific or other domain knowledge
5. **No Rollback Mechanism** - Cannot easily revert to a previous task's state

---

## Improvement Plan

### Phase 1: Task-Specific Agent Prompt Interface

**Goal**: Enable injection of domain-specific prompts for different task types.

#### 1.1 Create `AgentConfig` Class
```python
# config.py (new file)
@dataclass
class AgentConfig:
    """Configuration for domain-specific agent behavior."""

    # Planner prompts
    planner_system_prompt: str  # System prompt for planning
    planner_task_template: Optional[str] = None  # Template for task generation (optional)

    # Executor prompts
    executor_system_prompt: str = ""  # System prompt for execution
    executor_task_template: Optional[str] = None  # Template for task execution (optional)

    # Refiner prompts
    refiner_system_prompt: str = ""  # System prompt for refinement

    # Domain context
    domain_knowledge: str  # Background knowledge for the domain
    file_patterns: List[str]  # Relevant file patterns (e.g., "*.ets", "*.ts")

    # Behavior settings
    max_retries: int = 5
    background_task_timeout: int = 180  # 3 minutes of no output = stuck
```

#### 1.2 Create Config Registry
```python
# config_registry.py (new file)
class ConfigRegistry:
    """Registry for domain-specific configurations."""

    _configs: Dict[str, AgentConfig] = {}

    @classmethod
    def register(cls, name: str, config: AgentConfig):
        cls._configs[name] = config

    @classmethod
    def get(cls, name: str) -> Optional[AgentConfig]:
        return cls._configs.get(name)

    @classmethod
    def load_from_file(cls, path: str):
        """Load config from YAML/JSON file."""
```

#### 1.3 Built-in Configurations
- `coding` - Default software development config
- `harmonyos` - HarmonyOS app adapter development config
- `data` - Data processing pipeline config

### Phase 2: Enhanced Retry Mechanism

**Goal**: Implement intelligent retry with exponential backoff and task breakdown.

#### 2.1 Task Retry Tracker
```python
# retry_manager.py (new file)
@dataclass
class RetryState:
    task_id: str
    attempt_count: int
    last_error: str
    last_attempt_time: datetime
    retry_history: List[Dict]  # Previous attempts and their outcomes

class RetryManager:
    """Manages retry logic for failed tasks."""

    MAX_RETRIES = 5

    def should_retry(self, task_id: str, error: str) -> bool:
        """Determine if task should be retried."""

    def record_attempt(self, task_id: str, error: str, success: bool):
        """Record an attempt for tracking."""

    def get_retry_prompt_modifier(self, task_id: str) -> str:
        """Generate prompt modifier based on retry history."""
```

#### 2.2 Retry Strategy
1. **Attempt 1-3**: Retry same task with error context
2. **Attempt 4-5**: Retry with simplified approach prompt
3. **After 5 failures**: Break down into subtasks using Refiner

#### 2.3 Integration in Agent
```python
# In agent.py run() method
def execute_task_with_retry(self, task: SubTask, max_retries: int = 5) -> bool:
    for attempt in range(max_retries):
        try:
            success = self._execute_task_once(task, attempt)
            if success:
                return True

            # Record failure and get guidance
            self.retry_manager.record_attempt(task.id, last_error, False)
            retry_modifier = self.retry_manager.get_retry_prompt_modifier(task.id)

            if attempt == max_retries - 1:
                # Break down task
                self._breakdown_failed_task(task)
                return False
        except Exception as e:
            # Handle exception
    return False
```

### Phase 3: Background Process Management

**Goal**: Handle long-running tasks without timeout failures.

#### 3.1 Background Process Manager
```python
# background_manager.py (new file)
import subprocess
import threading
import time
from typing import Optional, Callable
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ProcessState:
    pid: int
    command: str
    start_time: datetime
    last_output_time: datetime
    output_buffer: List[str]
    status: str  # 'running', 'completed', 'failed', 'stuck'

class BackgroundManager:
    """Manages long-running background processes."""

    STUCK_THRESHOLD_SECONDS = 180  # 3 minutes without output = stuck
    MAX_LIFETIME_SECONDS = 1800    # 30 minutes absolute max = timeout

    def __init__(self):
        self.processes: Dict[str, ProcessState] = {}
        self._lock = threading.Lock()

    def start_process(self, task_id: str, command: str, cwd: str) -> str:
        """Start a background process for a task."""

    def check_process(self, task_id: str) -> ProcessState:
        """Check process status and output."""

    def is_stuck(self, task_id: str) -> bool:
        """Check if process has been silent for too long."""

    def is_timeout(self, task_id: str) -> bool:
        """Check if process has exceeded max lifetime."""

    def kill_process(self, task_id: str):
        """Terminate a stuck or timed-out process."""

    def get_output(self, task_id: str) -> str:
        """Get accumulated output from process."""
```

#### 3.2 Smart Execution Strategy
```python
# In executor.py
class Executor:
    def __init__(self, project_dir: str, background_manager: BackgroundManager):
        self.project_dir = project_dir
        self.background_manager = background_manager
        self._timeout_history: Dict[str, List[int]] = {}

    def run_command(self, command: str, task_id: str,
                    timeout: Optional[int] = None,
                    previous_timeout: bool = False) -> tuple[int, str]:
        """
        Run command with smart timeout handling.

        If previous_timeout is True, run as background process and poll.
        """
        if previous_timeout:
            return self._run_background(command, task_id, timeout)
        else:
            return self._run_foreground(command, timeout)
```

#### 3.3 Output Polling Loop
```python
def _run_background(self, command: str, task_id: str,
                    poll_interval: int = 30) -> tuple[int, str]:
    """Run command in background and poll for output."""
    self.background_manager.start_process(task_id, command, self.project_dir)

    while True:
        time.sleep(poll_interval)
        state = self.background_manager.check_process(task_id)

        if state.status == 'completed':
            return 0, self.background_manager.get_output(task_id)
        elif state.status == 'failed':
            return 1, self.background_manager.get_output(task_id)
        elif self.background_manager.is_timeout(task_id):
            # Max lifetime exceeded (30 min)
            self.background_manager.kill_process(task_id)
            return -1, f"Process timeout (exceeded {self.background_manager.MAX_LIFETIME_SECONDS}s)"
        elif self.background_manager.is_stuck(task_id):
            # is_stuck() fires after STUCK_THRESHOLD_SECONDS (3 min) of no output;
            # kill immediately so total silence-to-kill time stays at 3 minutes.
            self.background_manager.kill_process(task_id)
            return -1, "Process stuck (no output for 3 minutes)"
```

### Phase 4: Rollback Mechanism

**Goal**: Enable easy rollback to any task checkpoint using git commits.

#### 4.1 Core Principle
**Every successful task creates a commit**, serving as a natural checkpoint. Failed tasks do NOT commit, preserving the last known good state.

#### 4.2 Commit Format
```
[task-{id}] {title}

Task ID: {task_id}
Description: {description}
Test Command: {test_command}

Files changed:
- path/to/file1.ts
- path/to/file2.ts

Co-Authored-By: Autonomous Agent <agent@autonomous.dev>
```

#### 4.3 Rollback Manager
```python
# rollback_manager.py (new file)
from typing import Optional, List
from dataclasses import dataclass
import subprocess

@dataclass
class TaskCheckpoint:
    task_id: str
    commit_hash: str
    timestamp: str
    message: str

class RollbackManager:
    """Manages task checkpoints and rollback operations."""

    def __init__(self, project_dir: str):
        self.project_dir = project_dir

    def get_checkpoints(self) -> List[TaskCheckpoint]:
        """Get all task checkpoints from git history."""
        result = subprocess.run(
            ['git', 'log', '--grep=^\\[task-', '--oneline', '--format=%H|%ci|%s'],
            capture_output=True, text=True, cwd=self.project_dir
        )

        checkpoints = []
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = line.split('|')
                if len(parts) >= 3:
                    # Extract task ID from message like "[task-1-2] Title"
                    msg = parts[2]
                    task_id = self._extract_task_id(msg)
                    checkpoints.append(TaskCheckpoint(
                        task_id=task_id,
                        commit_hash=parts[0],
                        timestamp=parts[1],
                        message=msg
                    ))
        return checkpoints

    def rollback_to_task(self, task_id: str, keep_changes: bool = False) -> bool:
        """
        Rollback to the state after a specific task completed.

        Args:
            task_id: The task ID to rollback to
            keep_changes: If True, stash changes; if False, discard them

        Returns:
            True if rollback succeeded
        """
        checkpoints = self.get_checkpoints()
        target = next((c for c in checkpoints if c.task_id == task_id), None)

        if not target:
            print(f"No checkpoint found for task {task_id}")
            return False

        if keep_changes:
            subprocess.run(['git', 'stash'], cwd=self.project_dir)

        result = subprocess.run(
            ['git', 'reset', '--hard', target.commit_hash],
            cwd=self.project_dir
        )

        return result.returncode == 0

    def get_current_task_checkpoint(self) -> Optional[TaskCheckpoint]:
        """Get the most recent task checkpoint."""
        checkpoints = self.get_checkpoints()
        return checkpoints[0] if checkpoints else None

    def list_rollback_points(self) -> str:
        """Get formatted list of rollback points."""
        checkpoints = self.get_checkpoints()
        lines = ["Available rollback points:"]
        for i, cp in enumerate(checkpoints[:20], 1):  # Show last 20
            lines.append(f"  {i}. [{cp.task_id}] {cp.timestamp[:10]} - {cp.message[:50]}")
        return '\n'.join(lines)

    def _extract_task_id(self, message: str) -> str:
        """Extract task ID from commit message."""
        import re
        match = re.search(r'\[task-([^\]]+)\]', message)
        return match.group(1) if match else "unknown"
```

#### 4.4 CLI Rollback Commands
```python
# cli.py additions
def add_rollback_commands(parser):
    subparsers = parser.add_subparsers(dest='rollback_command')

    # List rollback points
    list_parser = subparsers.add_parser('list', help='List available rollback points')

    # Rollback to specific task
    to_parser = subparsers.add_parser('to', help='Rollback to a specific task')
    to_parser.add_argument('task_id', help='Task ID to rollback to')
    to_parser.add_argument('--keep', action='store_true', help='Stash changes instead of discarding')

    # Rollback to previous task
    prev_parser = subparsers.add_parser('prev', help='Rollback to previous task')
    prev_parser.add_argument('--keep', action='store_true', help='Stash changes instead of discarding')

# Usage:
# autonomous-coding rollback list
# autonomous-coding rollback to 1-2 --keep
# autonomous-coding rollback prev
```

#### 4.5 Integration with Agent
```python
# In agent.py - after successful task completion
def _commit_task_changes(self, task: SubTask, diff: str):
    """Commit changes with task checkpoint format."""
    commit_message = f"""[task-{task.id}] {task.title}

Task ID: {task.id}
Description: {task.description}
Test Command: {task.test_command}

Files changed:
{self._format_changed_files(diff)}

Co-Authored-By: Autonomous Agent <agent@autonomous.dev>
"""
    self.git_manager.commit(commit_message)
```

### Phase 5: HarmonyOS-Specific Configuration

**Goal**: Create HarmonyOS adapter development configuration.

#### 5.1 HarmonyOS Config File
```yaml
# configs/harmonyos.yaml
name: harmonyos
domain_knowledge: |
  HarmonyOS Application Development Context:
  - Uses ArkTS (TypeScript-based) for UI development
  - File extension: .ets (ArkTS)
  - Project structure: entry/, features/, common/
  - Build system: Hvigor (similar to Gradle)
  - Key APIs: @ohos.*, @arkui.*
  - State management: @State, @Prop, @Link decorators
  - Component lifecycle: aboutToAppear, aboutToDisappear

planner_system_prompt: |
  You are a HarmonyOS application architect. Plan tasks considering:
  - ArkTS component structure
  - HarmonyOS API capabilities
  - Module dependencies
  - Hvigor build requirements

executor_system_prompt: |
  You are a HarmonyOS developer. Implement features using:
  - ArkTS syntax and decorators
  - HarmonyOS SDK APIs
  - Proper component lifecycle

file_patterns:
  - "**/*.ets"
  - "**/build-profile.json5"
  - "**/hvigorfile.ts"
  - "**/oh-package.json5"

test_commands:
  unit: "hvigorw test"
  build: "hvigorw assembleHap"
  lint: "hvigorw lint"
```

#### 5.1 Config Loader
```python
# config_loader.py (new file)
import yaml
from pathlib import Path

def load_config(config_path: str) -> AgentConfig:
    """Load agent configuration from YAML file."""
    with open(config_path) as f:
        data = yaml.safe_load(f)

    return AgentConfig(
        planner_system_prompt=data.get('planner_system_prompt', ''),
        executor_system_prompt=data.get('executor_system_prompt', ''),
        refiner_system_prompt=data.get('refiner_system_prompt', ''),
        domain_knowledge=data.get('domain_knowledge', ''),
        file_patterns=data.get('file_patterns', ['*']),
        max_retries=data.get('max_retries', 5),
        background_task_timeout=data.get('background_task_timeout', 180)
    )
```

### Phase 6: Updated Agent Architecture

**Goal**: Refactor agent to use configurable components.

#### 6.1 New Agent Class
```python
# agent.py (refactored)
class AutonomousAgent:
    """Configurable autonomous agent for various task types."""

    def __init__(
        self,
        requirement: Optional[str],
        project_dir: Path,
        coding_tool: CodingTool,
        config: Optional[AgentConfig] = None
    ):
        self.requirement = requirement
        self.project_dir = project_dir
        self.coding_tool = coding_tool
        self.config = config or ConfigRegistry.get('coding')

        self.task_manager = TaskManager(project_dir)
        self.executor = Executor(str(project_dir), BackgroundManager())
        self.git_manager = GitManager(str(project_dir))
        self.refiner = TaskRefiner(self.coding_tool, self.config)
        self.retry_manager = RetryManager()

    def plan(self):
        """Plan tasks using domain-specific configuration."""
        planner_prompt = self._build_planner_prompt()

        if self.config.domain_knowledge:
            planner_prompt = f"{self.config.domain_knowledge}\n\n{planner_prompt}"

        # ... rest of planning logic

    def run(self, max_tasks: Optional[int] = None):
        """Execute tasks with retry and background handling."""
        # Use self.config.max_retries
        # Use self.config.background_task_timeout
        # Use self.executor with background support
```

#### 6.2 File Context Enhancement
```python
def get_file_context(self) -> str:
    """Get codebase context filtered by domain patterns."""
    file_context = ""

    for pattern in self.config.file_patterns:
        for file_path in self.project_dir.glob(pattern):
            if self._should_include_file(file_path):
                content = self._read_file(file_path)
                file_context += f"\nFILE: {file_path.relative_to(self.project_dir)}\n---\n{content}\n---\n"

    return file_context
```

---

## File Structure After Changes

```
autonomous-coding/
├── SKILL.md                    # Updated documentation
├── __init__.py
├── agent.py                    # Refactored with config support
├── background_manager.py       # NEW: Background process management
├── cli.py                      # Updated CLI with config + rollback options
├── coding_tool.py              # Unchanged
├── config.py                   # NEW: AgentConfig dataclass
├── config_loader.py            # NEW: YAML config loader
├── config_registry.py          # NEW: Config registry
├── executor.py                 # Enhanced with background support
├── git_manager.py              # Unchanged
├── refiner.py                  # Updated with config support
├── retry_manager.py            # NEW: Retry logic
├── rollback_manager.py         # NEW: Rollback mechanism
├── task.py                     # Unchanged
├── task_manager.py             # Unchanged
├── requirements.txt            # Updated dependencies
└── configs/
    ├── coding.yaml             # Default coding config
    └── harmonyos.yaml          # HarmonyOS-specific config
```

---

## Implementation Order

| Phase | Priority | Effort | Dependencies |
|-------|----------|--------|--------------|
| Phase 1: Config Interface | High | Medium | None |
| Phase 3: Background Manager | High | High | None |
| Phase 4: Rollback Mechanism | High | Low | None |
| Phase 2: Retry Mechanism | Medium | Medium | Phase 1 |
| Phase 6: Agent Refactor | High | High | Phase 1, 2, 3, 4 |
| Phase 5: HarmonyOS Config | Medium | Low | Phase 1, 6 |

---

## Backward Compatibility

- Default behavior (no config specified) remains identical to current
- Existing `tasks.json` format is preserved
- CLI arguments remain compatible
- New `--config` flag for specifying domain config
- New `rollback` subcommand for rollback operations

---

## Testing Strategy

1. **Unit Tests**: Each new component (RetryManager, BackgroundManager, ConfigLoader, RollbackManager)
2. **Integration Tests**: Full workflow with each config type
3. **Rollback Tests**: Verify rollback to various task checkpoints
4. **E2E Tests**: HarmonyOS adapter development scenario

---

## Success Criteria

1. ✅ Can inject HarmonyOS-specific knowledge for planning
2. ✅ Failed tasks retry up to 5 times before breakdown
3. ✅ Long-running commands run as background processes
4. ✅ Processes with no output for 3 minutes are marked as stuck
5. ✅ Processes exceeding 30 minutes are marked as timeout
6. ✅ Original task ID naming rules preserved
7. ✅ Each successful task creates a commit checkpoint
8. ✅ Can rollback to any task checkpoint via CLI
9. ✅ Can build HarmonyOS app adapter using this skill

---

## Next Steps

1. Review and approve this plan
2. Create implementation branch
3. Implement Phase 1 (Config Interface)
4. Implement Phase 3 (Background Manager)
5. Implement Phase 4 (Rollback Mechanism)
6. Implement Phase 2 (Retry Mechanism)
7. Refactor Agent (Phase 6)
8. Create HarmonyOS config (Phase 5)
9. Test with HarmonyOS adapter development
