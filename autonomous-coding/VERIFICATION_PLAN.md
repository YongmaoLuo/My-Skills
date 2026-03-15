# Verification Plan: `feat/autonomous-coding-improvements`

## What This Plan Covers

Two guarantees must hold after this feature branch is merged:

1. **Fatal failure detection works** — a task that fails 3 times across runs gets
   status `"fatal"`, has `failure_reason` written per-task, and the top-level
   `stop_reason`/`reason_detail` fields are written to `tasks.json`. The run stops
   with a human-readable intervention message.
2. **End-to-end workflow is unbroken** — the normal planning → execution → commit
   path still works, and on clean completion `stop_reason` is `"success"`.

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
| `"success"` | All tasks completed with no fatal | `null` |
| `"repeated_failure"` | A task reached `MAX_TASK_ERRORS` (3) | `"Task [id] failed N times. <last_error>"` |
| `null` | Run still in progress or interrupted externally | `null` |

Per-task fields added by this feature:

| Field | Type | Meaning |
|---|---|---|
| `error_count` | int | Number of times this task has exhausted all in-run retries across runs |
| `last_error` | str \| null | Most recent error message (truncated to 1000 chars) |
| `failure_reason` | str \| null | Set when `status = "fatal"` — why autonomous-coding gave up on this task |

---

## Key Implementation Facts (Code Map)

- `TaskManager.MAX_TASK_ERRORS = 3`
- `record_task_error(id, error)`: increments `error_count`, caps `last_error` at 1000 chars.
  At threshold → `status="fatal"`, writes `failure_reason`, returns `True`. Below threshold →
  `status="pending"`, returns `False`.
- `set_stop_reason(reason, detail)`: sets top-level `stop_reason`/`reason_detail` and saves.
- `run()`: calls `set_stop_reason("repeated_failure", ...)` on `FatalTaskError`; calls
  `set_stop_reason("success")` when `get_next_task()` returns `None`.
- `get_next_task()`: skips `"fatal"` and `"completed"` — only returns `"pending"` or `"in_progress"`.
- `_execute_task_with_retry()`: calls `record_task_error()` once per in-run retry exhaustion;
  raises `FatalTaskError` if fatal threshold reached.

---

## Part A: Automated Unit Tests (80 tests)

### A.1 Run the Full Suite

```bash
cd /Users/yongmaoluo/Documents/GitHub/My-Skills/autonomous-coding
python3 -m pytest tests/ -v --tb=short 2>&1 | tee pytest_output.txt
echo "Exit code: $?"
```

**Expected**: 80/80 passed, exit code 0.

**Critical tests:**

| Test | What It Verifies |
|---|---|
| `TestRecordTaskError::test_returns_true_at_threshold` | `record_task_error` returns `True` at count=3 |
| `TestRecordTaskError::test_fatal_persists_to_file` | `status="fatal"` + `failure_reason` survive a `TaskManager` reload |
| `TestRecordTaskError::test_truncates_long_error` | 1000-char cap on `last_error` |
| `TestExecuteTaskFailure::test_raises_fatal_error_after_max_persistent_failures` | Agent raises `FatalTaskError` at threshold |
| `TestExecuteTaskFailure::test_fatal_task_has_failure_reason_in_tasks_json` | `tasks.json` on disk has `failure_reason` after fatal |
| `TestRunLoop::test_run_stops_on_fatal_task` | Second task stays `"pending"` when first goes fatal |
| `TestRunLoop::test_run_skips_fatal_tasks_on_recover` | Pre-existing fatal task skipped; next task completes |
| `TestClaudeCodingTool::test_query_calls_claude_cli` | `--dangerously-skip-permissions` and `-p` are in the subprocess command |

### A.2 Gap Unit Scenarios (add to existing test files)

**A2-1 — `get_next_task` skips `"failed"` status:**
```python
def test_skips_failed_task(self):
    _, tm = _make_manager([_task_dict(id="1", status="failed")])
    assert tm.get_next_task() is None
```

**A2-2 — `[completed, fatal, pending]` returns the pending task:**
```python
def test_returns_pending_after_fatal_and_completed(self):
    data = [_task_dict(id="1", status="completed"),
            _task_dict(id="2", status="fatal"),
            _task_dict(id="3", status="pending")]
    _, tm = _make_manager(data)
    assert tm.get_next_task().id == "3"
```

**A2-3 — `record_task_error` with non-existent task ID:**
```python
def test_nonexistent_task_id_returns_false(self):
    _, tm = _make_manager([_task_dict(id="1")])
    assert tm.record_task_error("999", "err") is False
    assert tm.tasks[0].error_count == 0
```

**A2-4 — `error_count` already at threshold on load still triggers fatal:**
```python
def test_error_count_beyond_threshold_still_triggers_fatal(self):
    _, tm = _make_manager([_task_dict(id="1", error_count=3)])
    assert tm.record_task_error("1", "err") is True
    assert tm.tasks[0].status == "fatal"
```

**A2-5 — `"in_progress"` task reset to `"pending"` below threshold:**
```python
def test_in_progress_task_reset_to_pending_below_threshold(self):
    _, tm = _make_manager([_task_dict(id="1", status="in_progress", error_count=1)])
    tm.record_task_error("1", "err")
    assert tm.tasks[0].status == "pending"
    assert tm.tasks[0].error_count == 2
```

**A2-6 — `set_stop_reason` persists to disk and is reloaded:**
```python
def test_set_stop_reason_persists(self):
    path, tm = _make_manager([_task_dict(id="1")])
    tm.set_stop_reason("repeated_failure", "Task [1] failed 3 times. error msg")
    tm2 = TaskManager(path)
    assert tm2.stop_reason == "repeated_failure"
    assert "Task [1]" in tm2.reason_detail

def test_set_stop_reason_success(self):
    path, tm = _make_manager([_task_dict(id="1")])
    tm.set_stop_reason("success")
    tm2 = TaskManager(path)
    assert tm2.stop_reason == "success"
    assert tm2.reason_detail is None
```

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
    Returns the final tasks.json dict.
    """
    tmp = Path(tempfile.mkdtemp())
    (tmp / "tasks.json").write_text(json.dumps(tasks_json))
    # git init so GitManager doesn't fail
    import subprocess; subprocess.run(["git", "init"], cwd=tmp, capture_output=True)
    subprocess.run(["git", "commit", "--allow-empty", "-m", "init"], cwd=tmp, capture_output=True)

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
    agent.executor.run_command = mock_run_command
    agent.run(timeout=None)

    return json.loads((tmp / "tasks.json").read_text()), tmp
```

---

### B.1 — First-Run Failure Accumulation (error_count = 1, not yet fatal)

**Fixture** (`tasks.json`):
```json
{
  "requirement": "test failure tracking",
  "stop_reason": null, "reason_detail": null,
  "tasks": [{
    "id": "1", "title": "Task that fails", "description": "will fail",
    "test_command": "exit 1", "status": "pending",
    "error_count": 0, "last_error": null, "failure_reason": null, "updated_time": null
  }]
}
```

**Executor mock**: always returns `(1, "compile error on line 5")`.
**`max_retries=1`** to exhaust in one attempt.

**Expected `tasks.json` after run:**
```json
{
  "stop_reason": null,
  "reason_detail": null,
  "tasks": [{ "id": "1", "status": "pending", "error_count": 1,
              "last_error": "compile error on line 5", "failure_reason": null }]
}
```

**Checks:**
- `stop_reason` is still `null` (not fatal yet — needs 2 more failures).
- `error_count == 1`.
- `failure_reason` is `null`.
- `status == "pending"` (ready to retry in the next run).

---

### B.2 — Second-Run Failure Accumulation (error_count = 2, not yet fatal)

**Fixture**: Same as B.1 output — i.e., `error_count=1, status="pending"`.
```json
{
  "requirement": "test failure tracking",
  "stop_reason": null, "reason_detail": null,
  "tasks": [{
    "id": "1", "title": "Task that fails", "description": "will fail",
    "test_command": "exit 1", "status": "pending",
    "error_count": 1, "last_error": "compile error on line 5",
    "failure_reason": null, "updated_time": "2026-03-15T00:00:00"
  }]
}
```

**Executor mock**: `(1, "undefined symbol foo")`.

**Expected `tasks.json` after run:**
```json
{
  "stop_reason": null,
  "reason_detail": null,
  "tasks": [{ "id": "1", "status": "pending", "error_count": 2,
              "last_error": "undefined symbol foo", "failure_reason": null }]
}
```

**Checks:**
- `error_count == 2`.
- `stop_reason` is still `null`.
- `last_error` updated to the new error message.

---

### B.3 — Third-Run Fatal Trigger (PRIMARY FEATURE)

**Fixture**: B.2 output — `error_count=2, status="pending"`.
```json
{
  "requirement": "test failure tracking",
  "stop_reason": null, "reason_detail": null,
  "tasks": [{
    "id": "1", "title": "Task that fails", "description": "will fail",
    "test_command": "exit 1", "status": "pending",
    "error_count": 2, "last_error": "undefined symbol foo",
    "failure_reason": null, "updated_time": "2026-03-15T00:00:00"
  }]
}
```

**Executor mock**: `(1, "linker error: missing library")`.

**Expected `tasks.json` after run:**
```json
{
  "stop_reason": "repeated_failure",
  "reason_detail": "Task [1] failed 3 times. Task failed 3 times and could not be resolved automatically. Last error: linker error: missing library",
  "tasks": [{
    "id": "1", "status": "fatal", "error_count": 3,
    "last_error": "linker error: missing library",
    "failure_reason": "Task failed 3 times and could not be resolved automatically. Last error: linker error: missing library"
  }]
}
```

**Checks:**
- `stop_reason == "repeated_failure"`.
- `reason_detail` is non-null and contains `"Task [1]"` and the error text.
- Per-task: `status == "fatal"`, `error_count == 3`, `failure_reason` non-null.
- Stdout contains the intervention banner with `"HUMAN INTERVENTION REQUIRED"`.

---

### B.4 — Multi-Task Run: Fatal on Task 1 Does Not Touch Task 2

**Fixture**: Two tasks — task 1 at `error_count=2`, task 2 at `error_count=0`:
```json
{
  "requirement": "two tasks",
  "stop_reason": null, "reason_detail": null,
  "tasks": [
    { "id": "1", "title": "Fatal task", "description": "breaks", "test_command": "exit 1",
      "status": "pending", "error_count": 2, "last_error": "prev error",
      "failure_reason": null, "updated_time": null },
    { "id": "2", "title": "Healthy task", "description": "works", "test_command": "echo ok",
      "status": "pending", "error_count": 0, "last_error": null,
      "failure_reason": null, "updated_time": null }
  ]
}
```

**Executor mock**: always returns `(1, "fatal error msg")`.

**Expected `tasks.json` after run:**
```json
{
  "stop_reason": "repeated_failure",
  "reason_detail": "Task [1] failed 3 times. ...",
  "tasks": [
    { "id": "1", "status": "fatal", "error_count": 3 },
    { "id": "2", "status": "pending", "error_count": 0 }
  ]
}
```

**Checks:**
- Task 2 `status` unchanged (`"pending"`) — run stopped before reaching it.
- `coding_tool.query` called only once (for task 1 only).

---

### B.5 — Recovery with `--recover` After Fatal (`stop_reason` rewritten to `"success"`)

**Fixture**: Task 1 fatal, task 2 pending:
```json
{
  "requirement": "recovery test",
  "stop_reason": "repeated_failure",
  "reason_detail": "Task [1] failed 3 times. ...",
  "tasks": [
    { "id": "1", "title": "Broken", "description": "...", "test_command": "exit 1",
      "status": "fatal", "error_count": 3, "last_error": "...",
      "failure_reason": "Task failed 3 times...", "updated_time": "..." },
    { "id": "2", "title": "Healthy", "description": "...", "test_command": "echo ok",
      "status": "pending", "error_count": 0, "last_error": null,
      "failure_reason": null, "updated_time": null }
  ]
}
```

**Run with `recover=True`**, executor returns `(0, "Tests passed")` for task 2.

**Expected `tasks.json` after run:**
```json
{
  "stop_reason": "success",
  "reason_detail": null,
  "tasks": [
    { "id": "1", "status": "fatal", "error_count": 3 },
    { "id": "2", "status": "completed", "error_count": 0 }
  ]
}
```

**Checks:**
- `stop_reason` overwritten from `"repeated_failure"` → `"success"` (all non-fatal tasks done).
- `reason_detail` is `null`.
- Task 1 unchanged (fatal stays fatal).
- Task 2 completed; `git_manager.commit` called once.

---

### B.6 — Happy Path: All Tasks Succeed (`stop_reason = "success"`)

**Fixture**: Two fresh pending tasks:
```json
{
  "requirement": "build something",
  "stop_reason": null, "reason_detail": null,
  "tasks": [
    { "id": "1", "title": "Step 1", "description": "...", "test_command": "echo ok",
      "status": "pending", "error_count": 0, "last_error": null,
      "failure_reason": null, "updated_time": null },
    { "id": "2", "title": "Step 2", "description": "...", "test_command": "echo ok",
      "status": "pending", "error_count": 0, "last_error": null,
      "failure_reason": null, "updated_time": null }
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
    { "id": "1", "status": "completed", "error_count": 0, "failure_reason": null },
    { "id": "2", "status": "completed", "error_count": 0, "failure_reason": null }
  ]
}
```

**Checks:**
- `stop_reason == "success"`.
- `reason_detail` is `null`.
- Both tasks completed; `git_manager.commit` called twice.
- No `FatalTaskError` raised.
- `error_count` and `failure_reason` both untouched (0 / null) — new fields must not
  interfere with the normal workflow.

---

### B.7 — Cross-Run Context Injection (Previous Error Surfaced in Prompt)

**Fixture**: Task with `error_count=1` and a recorded `last_error`:
```json
{
  "requirement": "context injection test",
  "stop_reason": null, "reason_detail": null,
  "tasks": [{
    "id": "1", "title": "Retry task", "description": "needs context from last run",
    "test_command": "echo ok", "status": "pending",
    "error_count": 1, "last_error": "TypeError: cannot unpack non-sequence int",
    "failure_reason": null, "updated_time": "2026-03-15T00:00:00"
  }]
}
```

**Executor mock**: returns `(0, "Tests passed")` (task succeeds this time).

**Checks:**
- The prompt passed to `coding_tool.query` contains `"PREVIOUS RUN ERROR"` and
  `"TypeError: cannot unpack non-sequence int"` — the cross-run context was injected.
- After successful completion: `error_count` stays `1` (not reset), `status == "completed"`,
  `stop_reason == "success"`.

---

## Part C: Edge Cases

### C.1 — `last_error` Truncation at 1000 Characters

**Fixture**: Task with `error_count=0`. Executor returns `(1, "x" * 1001)`.

**Expected after run:**
- `len(task["last_error"]) == 1000`
- `tasks.json` is valid JSON (parse with `json.loads`)
- `reason_detail` (if fatal) embeds the truncated string without exceeding file sanity

### C.2 — `record_task_error` for Non-Existent Task ID

Call `record_task_error("999", "err")` on a manager with only task `"1"`.
- Returns `False`
- No task's `error_count` changes
- No exception raised
- `tasks.json` written successfully (save still called)

### C.3 — `[completed, fatal, pending]` — Correct Task Returned

**Fixture**:
```json
"tasks": [
  { "id": "1", "status": "completed", "error_count": 0 },
  { "id": "2", "status": "fatal",     "error_count": 3 },
  { "id": "3", "status": "pending",   "error_count": 0 }
]
```

`get_next_task()` must return task `"3"`. Tasks `"1"` and `"2"` must remain unchanged.

### C.4 — `stop_reason` Reflects the Actual Stop Cause

This tests all three `stop_reason` values in one fixture sequence:

| State | `stop_reason` | `reason_detail` |
|---|---|---|
| Mid-run (freshly created) | `null` | `null` |
| After `FatalTaskError` on task 1 | `"repeated_failure"` | contains `"Task [1]"` + error text |
| After `--recover` completes task 2 | `"success"` | `null` |

Use the B.3 → B.5 fixture chain. Verify each stage by reading `tasks.json` between runs.

### C.5 — `error_count` Already at Threshold in Fixture (`error_count=3, status="pending"`)

If the user manually edits `tasks.json` to set `error_count=3` but `status="pending"`,
the next `record_task_error` call sets `error_count=4` and still triggers fatal.

**Expected `failure_reason`**: contains `"4 times"` (correct: it incremented to 4 before checking `>= 3`).
**Expected `stop_reason`**: `"repeated_failure"`.

### C.6 — Fatal Task Never Left in `"in_progress"` State

After any fatal run, reload `TaskManager` from disk:
- `status == "fatal"` (not `"in_progress"`)
- `stop_reason == "repeated_failure"`
- `updated_time` is a valid ISO timestamp

### C.7 — `stop_reason` Not Overwritten When Run Is Interrupted Mid-Task

If the process is killed while a task is `"in_progress"`, `tasks.json` has no `stop_reason`
written yet (it's only written at clean stop points). On reload: `stop_reason == null`.
Simulate by calling `update_task_status("1", "in_progress")` then reading the file —
`stop_reason` must still be `null`.

---

## Part D: `tasks.json` State Reference

**Top-level fields after each transition:**

| Event | `stop_reason` | `reason_detail` |
|---|---|---|
| Freshly created / mid-run | `null` | `null` |
| Task fails (below threshold) | `null` | `null` |
| `FatalTaskError` raised | `"repeated_failure"` | `"Task [id] failed N times. <error>"` |
| All tasks complete | `"success"` | `null` |
| Recovery completes remaining tasks | `"success"` | `null` |

**Per-task fields at each state:**

| `status` | `error_count` | `last_error` | `failure_reason` |
|---|---|---|---|
| `"pending"` (no failures) | `0` | `null` | `null` |
| `"pending"` (failed once) | `1` | `"<msg>"` ≤1000 chars | `null` |
| `"pending"` (failed twice) | `2` | `"<msg>"` | `null` |
| `"fatal"` | `3` | `"<msg>"` | non-null, contains count + error |
| `"completed"` | `0` | `null` | `null` |

---

## Part E: Execution Order

1. **A.1** — Run all 80 existing tests. Must pass before continuing.
2. **A.2** — Add and run 6 gap unit tests (A2-1 through A2-6).
3. **B.6** — Happy path (baseline check — no failures, `stop_reason="success"`).
4. **B.1 → B.2 → B.3** — Run in sequence as a three-step fixture chain to verify cross-run accumulation.
5. **B.4** — Multi-task fatal stops at task 1, task 2 untouched.
6. **B.5** — Recovery overwrites `stop_reason` to `"success"`.
7. **B.7** — Cross-run context injection into the AI prompt.
8. **C.1–C.7** — Edge cases.

All scenarios in B and C verify state purely by reading `tasks.json`. No AI tool needs to run.
