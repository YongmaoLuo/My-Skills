# Verification Plan: `feat/autonomous-coding-improvements`

## What This Plan Covers

Two guarantees must hold after this feature branch is merged:

1. **Circular-loop detection works** — when the refiner creates a new task whose title
   matches an already-completed task, the system recognises it has already tried this fix
   but the problem recurred. It stops immediately, writes `stop_reason="repeated_failure"`
   and `reason_detail` to `tasks.json`, and prints a human-readable intervention banner.
2. **End-to-end workflow is unbroken** — the normal planning → execution → commit path
   still works, and on clean completion `stop_reason` is `"success"`.

---

## Detection Mechanism

The detection is **content-based, not status-based**. Before executing each task, the agent
checks whether a completed task with the same title already exists in `tasks.json`:

```
tasks.json (history) contains:
  { id: "1", title: "Fix null pointer in auth", status: "completed" }

Refiner adds a new task:
  { id: "1-2", title: "Fix null pointer in auth", status: "pending" }

→ Duplicate detected: the system already applied this fix.
  If the problem recurred, the agent cannot resolve it alone → STOP.
```

This catches the circular scenario: task fails → refiner breaks it into subtasks →
subtasks complete → problem persists → refiner creates the same subtask again.

---

## `tasks.json` Schema

Every run leaves a fully-described `tasks.json`:

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
| `"repeated_failure"` | Pending task duplicates a completed task | `"Task [id] '<title>' duplicates already-completed Task [id2]. ..."` |
| `null` | Run still in progress or externally interrupted | `null` |

Per-task fields:

| Field | Type | Meaning |
|---|---|---|
| `failure_reason` | str \| null | Set when `status = "failed"` — error output that caused failure (≤1000 chars) |

---

## Key Implementation Facts (Code Map)

- `find_completed_duplicate(task)`: iterates `self.tasks`; returns a `SubTask` with
  `status == "completed"` and `title == task.title` (different `id`), or `None`.
- `record_task_failure(id, error)`: marks `status="failed"`, sets `failure_reason`
  (truncated to 1000 chars), sets `updated_time`, saves to disk.
- `set_stop_reason(reason, detail)`: sets top-level `stop_reason`/`reason_detail` and saves.
- `run()`: before each `_execute_task_with_retry` call, checks `find_completed_duplicate()`.
  If a duplicate is found → `set_stop_reason("repeated_failure", ...)`, prints banner, breaks.
  On clean completion → `set_stop_reason("success")`.
- `get_next_task()`: returns `"pending"` or `"in_progress"` tasks only; skips `"failed"` and
  `"completed"`.
- `_execute_task_with_retry()`: on in-run retry exhaustion → calls `record_task_failure()`
  and returns `False`. The run continues with remaining tasks in the same run.

---

## Part A: Automated Unit Tests (88 tests)

### A.1 Run the Full Suite

```bash
cd /Users/yongmaoluo/Documents/GitHub/My-Skills/autonomous-coding
python3 -m pytest tests/ -v --tb=short 2>&1 | tee pytest_output.txt
echo "Exit code: $?"
```

**Expected**: 88/88 passed, exit code 0.

**Critical tests:**

| Test | What It Verifies |
|---|---|
| `TestFindCompletedDuplicate::test_returns_completed_task_with_same_title` | duplicate found when title matches completed task |
| `TestFindCompletedDuplicate::test_returns_none_when_no_completed_duplicate` | no false positive when matching task is "failed" not "completed" |
| `TestFindCompletedDuplicate::test_returns_none_when_different_title` | no false positive for different titles |
| `TestFindCompletedDuplicate::test_does_not_match_task_with_itself` | self-match excluded |
| `TestRunCircularLoopDetection::test_stops_when_pending_task_duplicates_completed_task` | pending task with duplicate title halts the run |
| `TestRunCircularLoopDetection::test_records_repeated_failure_stop_reason_on_circular_loop` | `stop_reason="repeated_failure"` written to disk |
| `TestRunCircularLoopDetection::test_no_false_positive_for_different_titles` | different title → run proceeds normally |
| `TestRunCircularLoopDetection::test_task_failing_within_run_then_continuing_others` | within one run, failing task marked failed, others complete |
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

### B.1 — Circular Loop Detection: Refiner Recreates a Completed Task (PRIMARY FEATURE)

**Scenario:** Task 1 ("Fix null pointer") was completed in a previous interaction. The
refiner now creates Task 2 with the same title, indicating the same problem recurred.

**Fixture** (`tasks.json`):
```json
{
  "requirement": "test circular loop",
  "stop_reason": null, "reason_detail": null,
  "tasks": [
    { "id": "1", "title": "Fix null pointer", "description": "add null check",
      "test_command": "echo ok", "status": "completed",
      "failure_reason": null, "updated_time": "2026-03-15T00:00:00" },
    { "id": "2", "title": "Fix null pointer", "description": "add null check again",
      "test_command": "echo ok", "status": "pending",
      "failure_reason": null, "updated_time": null }
  ]
}
```

**Executor mock**: `[(0, "Tests passed")]` (would only run if detection fails).

**Expected `tasks.json` after run:**
```json
{
  "stop_reason": "repeated_failure",
  "reason_detail": "Task [2] 'Fix null pointer' duplicates already-completed Task [1]. ...",
  "tasks": [
    { "id": "1", "status": "completed" },
    { "id": "2", "status": "pending" }
  ]
}
```

**Checks:**
- `stop_reason == "repeated_failure"`.
- `reason_detail` contains `"Fix null pointer"` and both task IDs.
- Task 2 `status` unchanged (`"pending"`) — was never executed.
- `executor.run_command` was **never called**.
- Stdout contains `"HUMAN INTERVENTION REQUIRED"`.

---

### B.2 — Multi-Step Circular Loop Chain

**Scenario:** Tasks 1 and 2 complete, then the refiner adds tasks 3 and 4. Task 3 has a
unique title (runs fine), but task 4 duplicates task 2's title.

**Fixture:**
```json
{
  "requirement": "multi-step loop",
  "stop_reason": null, "reason_detail": null,
  "tasks": [
    { "id": "1", "title": "Setup DB", "status": "completed",
      "failure_reason": null, "updated_time": "..." },
    { "id": "2", "title": "Run migrations", "status": "completed",
      "failure_reason": null, "updated_time": "..." },
    { "id": "3", "title": "Add index", "status": "pending",
      "failure_reason": null, "updated_time": null },
    { "id": "4", "title": "Run migrations", "status": "pending",
      "failure_reason": null, "updated_time": null }
  ]
}
```

**Executor mock**: `[(0, "Tests passed"), (0, "Tests passed")]`.

**Expected after run:**
- Task 3: `"completed"` (ran successfully — no duplicate).
- Task 4: `"pending"` (stopped before executing — duplicates task 2).
- `stop_reason == "repeated_failure"`.
- `executor.run_command` called exactly **once** (for task 3 only).

---

### B.3 — First-Run Failure: Task Marked `"failed"`, Run Continues

**Scenario:** Within a single run, a task fails all retries. It is marked "failed" but
other tasks continue. No circular loop detection should trigger.

**Fixture:**
```json
{
  "requirement": "test failure tracking",
  "stop_reason": null, "reason_detail": null,
  "tasks": [
    { "id": "1", "title": "Compile module", "description": "will fail",
      "test_command": "exit 1", "status": "pending",
      "failure_reason": null, "updated_time": null },
    { "id": "2", "title": "Run tests", "description": "will pass",
      "test_command": "echo ok", "status": "pending",
      "failure_reason": null, "updated_time": null }
  ]
}
```

**Executor mock**: `[(1, "compile error"), (0, "Tests passed")]`.

**Expected `tasks.json` after run:**
```json
{
  "stop_reason": "success",
  "reason_detail": null,
  "tasks": [
    { "id": "1", "status": "failed", "failure_reason": "compile error" },
    { "id": "2", "status": "completed", "failure_reason": null }
  ]
}
```

**Checks:**
- `stop_reason == "success"` — run completed; task 2 was not blocked.
- Task 1: `status == "failed"`, `failure_reason` contains the error text.
- Task 2: `status == "completed"`.

---

### B.4 — Happy Path: All Tasks Succeed (`stop_reason = "success"`)

**Fixture:** Two fresh pending tasks with distinct titles:
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

**Checks:**
- `stop_reason == "success"`, `reason_detail == null`.
- Both tasks `"completed"`, `failure_reason` null for both.
- `git_manager.commit` called twice.

---

### B.5 — No False Positive: Pending Task With Same Title But Different Status History

**Scenario:** Task 1 failed (not completed). Task 2 has the same title. No duplicate
should be detected since the match only triggers on `"completed"` tasks.

**Fixture:**
```json
{
  "requirement": "no false positive",
  "stop_reason": null, "reason_detail": null,
  "tasks": [
    { "id": "1", "title": "Fix auth", "status": "failed",
      "failure_reason": "build error", "updated_time": "..." },
    { "id": "2", "title": "Fix auth", "status": "pending",
      "failure_reason": null, "updated_time": null }
  ]
}
```

**Executor mock**: `[(0, "Tests passed")]`.

**Expected:** Task 2 runs and completes. `stop_reason == "success"`.

---

## Part C: Edge Cases

### C.1 — `failure_reason` Truncation at 1000 Characters

**Fixture:** Task with `status="pending"`. Executor returns `(1, "x" * 1001)`.

**Expected:**
- `len(task["failure_reason"]) == 1000`
- `tasks.json` is valid JSON

### C.2 — `find_completed_duplicate` With Non-Existent Task

Call `find_completed_duplicate` on a task that doesn't exist in the list — no exception.

### C.3 — Title Case Sensitivity

Titles `"Fix auth"` and `"fix auth"` must **not** match (exact string comparison).
A task with `"Fix auth"` completed and `"fix auth"` pending → task 2 should run.

### C.4 — `stop_reason` Reflects the Actual Stop Cause

| State | `stop_reason` | `reason_detail` |
|---|---|---|
| Freshly created / mid-run | `null` | `null` |
| Circular loop detected | `"repeated_failure"` | contains both task IDs and title |
| All unique tasks complete | `"success"` | `null` |

Use the B.1 fixture. Verify each stage by reading `tasks.json`.

### C.5 — `stop_reason` Not Overwritten When Run Is Interrupted Mid-Task

If the process is killed while a task is `"in_progress"`, `stop_reason` has not yet been
written. On reload: `stop_reason == null`. Simulate by calling
`update_task_status("1", "in_progress")` then reading the file directly.

### C.6 — Circular Loop Stop Does Not Execute Any Further Tasks

In B.1, `executor.run_command` must be called **zero times** (not just once). Verify the
mock's `call_count` is 0 after the run.

---

## Part D: `tasks.json` State Reference

**Top-level fields after each transition:**

| Event | `stop_reason` | `reason_detail` |
|---|---|---|
| Freshly created / mid-run | `null` | `null` |
| Task fails within a run (others may continue) | `null` | `null` |
| Circular loop detected (duplicate completed task) | `"repeated_failure"` | contains task IDs and title |
| All tasks complete | `"success"` | `null` |

**Per-task fields:**

| `status` | `failure_reason` |
|---|---|
| `"pending"` / `"in_progress"` | `null` |
| `"failed"` (exhausted in-run retries) | non-null, ≤1000 chars |
| `"completed"` | `null` |

---

## Part E: Execution Order

1. **A.1** — Run all 88 existing tests. Must pass before continuing.
2. **B.4** — Happy path baseline: all tasks complete, `stop_reason="success"`.
3. **B.3** — First-run failure: task fails, other tasks continue.
4. **B.1** — Circular loop detection: stopped before task 2 runs.
5. **B.2** — Multi-step chain: task 3 runs, task 4 stopped.
6. **B.5** — No false positive: "failed" status does not trigger detection.
7. **C.1–C.6** — Edge cases.

All scenarios in B and C verify state purely by reading `tasks.json`. No AI tool needs to run.
