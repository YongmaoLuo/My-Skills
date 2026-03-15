# Verification Plan: `feat/autonomous-coding-improvements`

## What This Plan Covers

Two guarantees must hold after this feature branch is merged:

1. **Repeated-failure detection works** — a task that fails in one run is marked `"failed"`
   with `failure_reason` written to disk. On the next run, detecting that failed task causes
   an immediate stop: `stop_reason="repeated_failure"` and `reason_detail` are written to
   `tasks.json`, and a human-readable intervention message is printed.
2. **End-to-end workflow is unbroken** — the normal planning → execution → commit path still
   works, and on clean completion `stop_reason` is `"success"`.

---

## `tasks.json` Schema

Every run leaves a fully-described `tasks.json`. The top-level structure is:

```json
{
  "requirement": "<original requirement string>",
  "stop_reason": "<success | repeated_failure | null>",
  "reason_detail": "<human-readable detail, or null>",
  "tasks": [ ... ]
}
```

| `stop_reason` | When written | `reason_detail` |
|---|---|---|
| `"success"` | All tasks completed | `null` |
| `"repeated_failure"` | A previously-failed task detected at run start | `"Task [id] '<title>' failed in a previous run. <failure_reason>"` |
| `null` | Run still in progress or interrupted externally | `null` |

Per-task fields:

| Field | Type | Meaning |
|---|---|---|
| `failure_reason` | str \| null | Set when `status = "failed"` — the error output that caused the failure (truncated to 1000 chars) |

---

## Key Implementation Facts (Code Map)

- `record_task_failure(id, error)`: marks `status="failed"`, sets `failure_reason` (truncated
  to 1000 chars), sets `updated_time`, saves to disk.
- `set_stop_reason(reason, detail)`: sets top-level `stop_reason`/`reason_detail` and saves.
- `run()`: at startup scans all tasks for `status == "failed"`. If any found → calls
  `set_stop_reason("repeated_failure", ...)`, prints intervention banner, returns immediately.
  On clean completion calls `set_stop_reason("success")`.
- `get_next_task()`: skips `"failed"` and `"completed"` — only returns `"pending"` or
  `"in_progress"` tasks.
- `_execute_task_with_retry()`: on in-run retry exhaustion → calls `record_task_failure()`
  and returns `False`. The run continues with remaining tasks in the same run.

---

## Part A: Automated Unit Tests (82 tests)

### A.1 Run the Full Suite

```bash
cd /Users/yongmaoluo/Documents/GitHub/My-Skills/autonomous-coding
python3 -m pytest tests/ -v --tb=short 2>&1 | tee pytest_output.txt
echo "Exit code: $?"
```

**Expected**: 82/82 passed, exit code 0.

**Critical tests:**

| Test | What It Verifies |
|---|---|
| `TestRecordTaskFailure::test_marks_task_failed` | `record_task_failure` sets `status="failed"` |
| `TestRecordTaskFailure::test_records_failure_reason` | `failure_reason` recorded on disk |
| `TestRecordTaskFailure::test_truncates_long_error` | 1000-char cap on `failure_reason` |
| `TestGetNextTask::test_skips_failed_task` | `get_next_task` skips `"failed"` tasks |
| `TestExecuteTaskFailure::test_marks_failed_after_all_retries` | task status is `"failed"` after retry exhaustion |
| `TestExecuteTaskFailure::test_records_failure_reason_in_tasks_json` | `failure_reason` in `tasks.json` after failure |
| `TestRunRepeatedFailureDetection::test_stops_immediately_when_failed_task_in_tasks_json` | second task untouched when run detects previous failure |
| `TestRunRepeatedFailureDetection::test_records_repeated_failure_stop_reason` | `stop_reason="repeated_failure"` written to disk |
| `TestRunRepeatedFailureDetection::test_first_run_can_fail_task_and_continue_others` | within one run, failing task marked failed but others complete |
| `TestRunLoop::test_sets_success_stop_reason_when_all_complete` | `stop_reason="success"` on clean completion |
| `TestClaudeCodingTool::test_query_calls_claude_cli` | `--dangerously-skip-permissions` and `-p` are in the subprocess command |

---

## Part B: Integration Scenarios Using Crafted `tasks.json` Fixtures

Each scenario is fully self-contained: create a `tasks.json` fixture in a temp directory,
run the agent (with `executor.run_command` mocked — **no AI tool invoked**), then inspect
`tasks.json` to verify the expected state.

**Common test harness:**
```python
import json, tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

def run_agent_with_fixture(tasks_json: dict, executor_returns: list):
    """
    executor_returns: list of (exit_code, output) tuples, consumed in order.
    Returns the final tasks.json dict and the tmp Path.
    """
    tmp = Path(tempfile.mkdtemp())
    (tmp / "tasks.json").write_text(json.dumps(tasks_json))

    from agent import AutonomousAgent
    from coding_tool import CodingTool
    from config_registry import ConfigRegistry

    mock_tool = MagicMock(spec=CodingTool)
    mock_tool.query.return_value = "No file changes."

    call_count = [0]
    def mock_run_command(cmd, **kwargs):
        idx = min(call_count[0], len(executor_returns) - 1)
        call_count[0] += 1
        return executor_returns[idx]

    with patch("agent.GitManager"):
        agent = AutonomousAgent(
            requirement=None,
            project_dir=tmp,
            coding_tool=mock_tool,
            config=ConfigRegistry.get("coding")
        )
    agent.config.max_retries = 1  # one attempt per task for predictable mocks
    agent.executor.run_command = mock_run_command
    agent.run(timeout=None)

    return json.loads((tmp / "tasks.json").read_text()), tmp
```

---

### B.1 — First-Run Failure: Task Marked `"failed"`, Run Continues

**Fixture** (`tasks.json`):
```json
{
  "requirement": "test failure tracking",
  "stop_reason": null, "reason_detail": null,
  "tasks": [
    { "id": "1", "title": "Failing task", "description": "will fail",
      "test_command": "exit 1", "status": "pending",
      "failure_reason": null, "updated_time": null },
    { "id": "2", "title": "Passing task", "description": "will pass",
      "test_command": "echo ok", "status": "pending",
      "failure_reason": null, "updated_time": null }
  ]
}
```

**Executor mock**: `[(1, "compile error on line 5"), (0, "Tests passed")]`.

**Expected `tasks.json` after run:**
```json
{
  "stop_reason": "success",
  "reason_detail": null,
  "tasks": [
    { "id": "1", "status": "failed", "failure_reason": "compile error on line 5" },
    { "id": "2", "status": "completed", "failure_reason": null }
  ]
}
```

**Checks:**
- `stop_reason == "success"` — run completed; task 2 was not blocked by task 1's failure.
- Task 1: `status == "failed"`, `failure_reason` contains the error text.
- Task 2: `status == "completed"`.

---

### B.2 — Second Run: Failed Task Detected, Immediate Stop (PRIMARY FEATURE)

**Fixture**: B.1 output — task 1 is `"failed"`, task 2 is `"completed"`. Add a new task 3.
```json
{
  "requirement": "test failure tracking",
  "stop_reason": "success", "reason_detail": null,
  "tasks": [
    { "id": "1", "title": "Failing task", "description": "will fail",
      "test_command": "exit 1", "status": "failed",
      "failure_reason": "compile error on line 5", "updated_time": "2026-03-15T00:00:00" },
    { "id": "2", "title": "Passing task", "description": "done",
      "test_command": "echo ok", "status": "completed",
      "failure_reason": null, "updated_time": "2026-03-15T00:00:01" },
    { "id": "3", "title": "New task", "description": "would run if not stopped",
      "test_command": "echo ok", "status": "pending",
      "failure_reason": null, "updated_time": null }
  ]
}
```

**Executor mock**: `[(0, "Tests passed")]` (would only be called if run doesn't stop early).

**Expected `tasks.json` after run:**
```json
{
  "stop_reason": "repeated_failure",
  "reason_detail": "Task [1] 'Failing task' failed in a previous run and failed again. compile error on line 5",
  "tasks": [
    { "id": "1", "status": "failed" },
    { "id": "2", "status": "completed" },
    { "id": "3", "status": "pending" }
  ]
}
```

**Checks:**
- `stop_reason == "repeated_failure"`.
- `reason_detail` is non-null and contains `"Task [1]"` and the error text.
- Task 3 `status` unchanged (`"pending"`) — run stopped before reaching it.
- `executor.run_command` was **never called** (run exited before the task loop).
- Stdout contains `"HUMAN INTERVENTION REQUIRED"`.

---

### B.3 — Multi-Task Run: Failed Task Detected Before Any Other Task Runs

**Fixture**: Task 1 failed from a previous run, tasks 2 and 3 pending:
```json
{
  "requirement": "multi-task test",
  "stop_reason": null, "reason_detail": null,
  "tasks": [
    { "id": "1", "title": "Broken", "description": "already failed",
      "test_command": "exit 1", "status": "failed",
      "failure_reason": "linker error", "updated_time": "2026-03-15T00:00:00" },
    { "id": "2", "title": "Task 2", "description": "pending",
      "test_command": "echo ok", "status": "pending",
      "failure_reason": null, "updated_time": null },
    { "id": "3", "title": "Task 3", "description": "pending",
      "test_command": "echo ok", "status": "pending",
      "failure_reason": null, "updated_time": null }
  ]
}
```

**Expected `tasks.json` after run:**
- `stop_reason == "repeated_failure"`.
- Tasks 2 and 3 both still `"pending"` — no tasks executed.

---

### B.4 — Happy Path: All Tasks Succeed (`stop_reason = "success"`)

**Fixture**: Two fresh pending tasks:
```json
{
  "requirement": "build something",
  "stop_reason": null, "reason_detail": null,
  "tasks": [
    { "id": "1", "title": "Step 1", "description": "...", "test_command": "echo ok",
      "status": "pending", "failure_reason": null, "updated_time": null },
    { "id": "2", "title": "Step 2", "description": "...", "test_command": "echo ok",
      "status": "pending", "failure_reason": null, "updated_time": null }
  ]
}
```

**Executor mock**: always returns `(0, "Tests passed")`.

**Expected `tasks.json` after run:**
```json
{
  "stop_reason": "success",
  "reason_detail": null,
  "tasks": [
    { "id": "1", "status": "completed", "failure_reason": null },
    { "id": "2", "status": "completed", "failure_reason": null }
  ]
}
```

**Checks:**
- `stop_reason == "success"`.
- Both tasks completed; `git_manager.commit` called twice.
- `failure_reason` untouched (null) — new fields must not interfere with normal workflow.

---

### B.5 — Recovery After Failed Task (User Fixes Issue, Re-runs)

User fixes the underlying issue and deletes or changes the failed task's status back to
`"pending"` before re-running. The run should proceed normally.

**Fixture**: Manually reset task 1 to `"pending"` (simulating user intervention):
```json
{
  "requirement": "recovery test",
  "stop_reason": "repeated_failure",
  "reason_detail": "Task [1] failed in a previous run...",
  "tasks": [
    { "id": "1", "title": "Fixed task", "description": "now works",
      "test_command": "echo ok", "status": "pending",
      "failure_reason": null, "updated_time": null }
  ]
}
```

**Executor mock**: `[(0, "Tests passed")]`.

**Expected `tasks.json` after run:**
```json
{
  "stop_reason": "success",
  "reason_detail": null,
  "tasks": [{ "id": "1", "status": "completed" }]
}
```

**Checks:**
- No `"failed"` tasks at startup → run proceeds normally.
- `stop_reason` overwritten from `"repeated_failure"` → `"success"`.

---

## Part C: Edge Cases

### C.1 — `failure_reason` Truncation at 1000 Characters

**Fixture**: Task with `status="pending"`. Executor returns `(1, "x" * 1001)`.

**Expected after run:**
- `len(task["failure_reason"]) == 1000`
- `tasks.json` is valid JSON (parse with `json.loads`)

### C.2 — `record_task_failure` for Non-Existent Task ID

Call `record_task_failure("999", "err")` on a manager with only task `"1"`.
- No exception raised
- Task `"1"` unchanged (`failure_reason` still null)
- `tasks.json` written successfully

### C.3 — `[completed, failed, pending]` — Correct Task Returned

**Fixture**:
```json
"tasks": [
  { "id": "1", "status": "completed" },
  { "id": "2", "status": "failed", "failure_reason": "old error" },
  { "id": "3", "status": "pending" }
]
```

BUT: since task 2 has `status="failed"`, `run()` detects it at startup and stops immediately.
`get_next_task()` called in isolation must return task `"3"` (the pending one).

### C.4 — `stop_reason` Reflects the Actual Stop Cause

Tests all three `stop_reason` values in a fixture sequence:

| State | `stop_reason` | `reason_detail` |
|---|---|---|
| Freshly created / mid-run | `null` | `null` |
| Run detects failed task at startup | `"repeated_failure"` | contains `"Task [1]"` + error text |
| User resets task to pending, re-runs, all complete | `"success"` | `null` |

Use the B.1 → B.2 → B.5 fixture chain. Verify each stage by reading `tasks.json` between runs.

### C.5 — Failed Task Never Left in `"in_progress"` State

After any run that marks a task `"failed"`, reload `TaskManager` from disk:
- `status == "failed"` (not `"in_progress"`)
- `updated_time` is a valid ISO timestamp

### C.6 — `stop_reason` Not Overwritten When Run Is Interrupted Mid-Task

If the process is killed while a task is `"in_progress"`, `stop_reason` has not yet been
written. On reload: `stop_reason == null`. Simulate by calling
`update_task_status("1", "in_progress")` then reading the file — `stop_reason` must still
be `null`.

---

## Part D: `tasks.json` State Reference

**Top-level fields after each transition:**

| Event | `stop_reason` | `reason_detail` |
|---|---|---|
| Freshly created / mid-run | `null` | `null` |
| Task fails within a run (others may continue) | `null` | `null` |
| Run detects a previously-failed task | `"repeated_failure"` | `"Task [id] '<title>' failed in a previous run. <failure_reason>"` |
| All tasks complete | `"success"` | `null` |
| User resets failed task, re-run completes | `"success"` | `null` |

**Per-task fields at each state:**

| `status` | `failure_reason` |
|---|---|
| `"pending"` (no failures) | `null` |
| `"failed"` (failed in this run) | non-null, ≤1000 chars |
| `"completed"` | `null` |

---

## Part E: Execution Order

1. **A.1** — Run all 82 existing tests. Must pass before continuing.
2. **B.4** — Happy path (baseline check — no failures, `stop_reason="success"`).
3. **B.1** — First-run failure: task 1 fails, task 2 completes, `stop_reason="success"`.
4. **B.2** — Second run with B.1 output: detected immediately, `stop_reason="repeated_failure"`.
5. **B.3** — Multi-task variant of the same detection.
6. **B.5** — User resets failed task, re-run succeeds, `stop_reason` flips to `"success"`.
7. **C.1–C.6** — Edge cases.

All scenarios in B and C verify state purely by reading `tasks.json`. No AI tool needs to run.
