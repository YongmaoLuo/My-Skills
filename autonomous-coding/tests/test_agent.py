"""Unit tests for AutonomousAgent — task execution, fatal stopping, and run loop."""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, call

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from task import SubTask
from task_manager import TaskManager
from agent import AutonomousAgent, FatalTaskError
from coding_tool import CodingTool
from config_registry import ConfigRegistry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_agent(tasks_data=None, requirement="req"):
    """Return an AutonomousAgent wired to a temp dir with mock coding tool."""
    tmp = Path(tempfile.mkdtemp())
    if tasks_data:
        with open(tmp / "tasks.json", "w") as f:
            json.dump({"requirement": requirement, "tasks": tasks_data}, f)

    coding_tool = MagicMock(spec=CodingTool)
    coding_tool.query.return_value = "No file changes."
    coding_tool.query_json.return_value = {"tasks": tasks_data or []}

    config = ConfigRegistry.get("coding")

    # Mock GitManager so tests don't need a real git repo
    with patch("agent.GitManager") as mock_git_cls:
        mock_git_cls.return_value = MagicMock()
        agent = AutonomousAgent(
            requirement=requirement,
            project_dir=tmp,
            coding_tool=coding_tool,
            config=config,
        )

    # Patch executor so no real commands run
    agent.executor.run_command = MagicMock(return_value=(0, "Tests passed"))
    return agent, tmp


def _task_dict(id="1", title="T", description="D", test_cmd="echo ok",
               status="pending", error_count=0):
    return {
        "id": id, "title": title, "description": description,
        "test_command": test_cmd, "status": status,
        "error_count": error_count, "last_error": None,
        "failure_reason": None, "updated_time": None,
    }


# ---------------------------------------------------------------------------
# FatalTaskError
# ---------------------------------------------------------------------------

class TestFatalTaskError:
    def test_attributes(self):
        err = FatalTaskError("task-1", "something broke")
        assert err.task_id == "task-1"
        assert err.reason == "something broke"
        assert "task-1" in str(err)


# ---------------------------------------------------------------------------
# _execute_task_with_retry — success path
# ---------------------------------------------------------------------------

class TestExecuteTaskSuccess:
    def test_marks_task_completed_on_success(self):
        agent, _ = _make_agent([_task_dict(id="1")])
        task = agent.task_manager.tasks[0]
        result = agent._execute_task_with_retry(task, max_retries=1)
        assert result is True
        assert agent.task_manager.tasks[0].status == "completed"

    def test_commits_on_success(self):
        agent, _ = _make_agent([_task_dict(id="1")])
        task = agent.task_manager.tasks[0]
        agent._execute_task_with_retry(task, max_retries=1)
        agent.git_manager.commit.assert_called_once()

    def test_resets_retry_state_on_success(self):
        agent, _ = _make_agent([_task_dict(id="1")])
        agent.retry_manager.record_attempt("1", "prev error", False)
        task = agent.task_manager.tasks[0]
        agent._execute_task_with_retry(task, max_retries=2)
        assert agent.retry_manager.get_state("1") is None


# ---------------------------------------------------------------------------
# _execute_task_with_retry — failure path
# ---------------------------------------------------------------------------

class TestExecuteTaskFailure:
    def test_returns_false_after_all_retries(self):
        agent, _ = _make_agent([_task_dict(id="1")])
        agent.executor.run_command = MagicMock(return_value=(1, "Build failed"))
        # Prevent refiner from changing tasks
        agent.refiner.refine = MagicMock(return_value=[_task_dict(id="1")])
        task = agent.task_manager.tasks[0]
        result = agent._execute_task_with_retry(task, max_retries=2)
        assert result is False

    def test_increments_error_count_on_exhausted_retries(self):
        agent, _ = _make_agent([_task_dict(id="1")])
        agent.executor.run_command = MagicMock(return_value=(1, "error"))
        agent.refiner.refine = MagicMock(return_value=[_task_dict(id="1")])
        task = agent.task_manager.tasks[0]
        agent._execute_task_with_retry(task, max_retries=1)
        assert agent.task_manager.tasks[0].error_count == 1

    def test_raises_fatal_error_after_max_persistent_failures(self):
        # Seed error_count at threshold - 1 so one more failure triggers fatal
        threshold = TaskManager.MAX_TASK_ERRORS
        agent, _ = _make_agent([_task_dict(id="1", error_count=threshold - 1)])
        agent.executor.run_command = MagicMock(return_value=(1, "persistent error"))
        agent.refiner.refine = MagicMock(return_value=[_task_dict(id="1", error_count=threshold - 1)])
        task = agent.task_manager.tasks[0]
        try:
            agent._execute_task_with_retry(task, max_retries=1)
            assert False, "Expected FatalTaskError"
        except FatalTaskError as e:
            assert e.task_id == "1"

    def test_fatal_task_has_failure_reason_in_tasks_json(self):
        threshold = TaskManager.MAX_TASK_ERRORS
        agent, tmp = _make_agent([_task_dict(id="1", error_count=threshold - 1)])
        agent.executor.run_command = MagicMock(return_value=(1, "fatal error msg"))
        agent.refiner.refine = MagicMock(return_value=[_task_dict(id="1", error_count=threshold - 1)])
        task = agent.task_manager.tasks[0]
        try:
            agent._execute_task_with_retry(task, max_retries=1)
        except FatalTaskError:
            pass
        # Reload from disk
        tm2 = TaskManager(tmp)
        assert tm2.tasks[0].status == "fatal"
        assert tm2.tasks[0].failure_reason is not None


# ---------------------------------------------------------------------------
# run() — loop control
# ---------------------------------------------------------------------------

class TestRunLoop:
    def test_run_completes_all_tasks(self):
        tasks = [_task_dict(id=str(i)) for i in range(3)]
        agent, _ = _make_agent(tasks)
        agent.run(timeout=None)
        assert all(t.status == "completed" for t in agent.task_manager.tasks)

    def test_run_stops_at_max_tasks(self):
        tasks = [_task_dict(id=str(i)) for i in range(5)]
        agent, _ = _make_agent(tasks)
        agent.run(max_tasks=2, timeout=None)
        completed = sum(1 for t in agent.task_manager.tasks if t.status == "completed")
        assert completed == 2

    def test_run_stops_on_fatal_task(self):
        threshold = TaskManager.MAX_TASK_ERRORS
        tasks = [
            _task_dict(id="1", error_count=threshold - 1),
            _task_dict(id="2"),
        ]
        agent, _ = _make_agent(tasks)
        agent.executor.run_command = MagicMock(return_value=(1, "fatal error"))
        agent.refiner.refine = MagicMock(return_value=tasks)
        agent.run(timeout=None)
        # Task 2 should never have been attempted (still pending)
        assert agent.task_manager.tasks[1].status == "pending"

    def test_run_skips_fatal_tasks_on_recover(self):
        """After a fatal, reloading with --recover should not re-attempt fatal tasks."""
        threshold = TaskManager.MAX_TASK_ERRORS
        agent, tmp = _make_agent([
            _task_dict(id="1", status="fatal", error_count=threshold),
            _task_dict(id="2"),
        ])
        agent.run(timeout=None)
        # Only task 2 should complete; task 1 stays fatal
        assert agent.task_manager.tasks[0].status == "fatal"
        assert agent.task_manager.tasks[1].status == "completed"


# ---------------------------------------------------------------------------
# plan()
# ---------------------------------------------------------------------------

class TestPlan:
    def test_plan_sets_tasks(self):
        agent, _ = _make_agent()
        agent.coding_tool.query_json.return_value = {
            "tasks": [_task_dict(id="1"), _task_dict(id="2")]
        }
        agent.plan()
        assert len(agent.task_manager.tasks) == 2

    def test_plan_stores_requirement(self):
        agent, _ = _make_agent(requirement="Build NFC app")
        agent.coding_tool.query_json.return_value = {"tasks": [_task_dict(id="1")]}
        agent.plan()
        assert agent.task_manager.requirement == "Build NFC app"


# ---------------------------------------------------------------------------
# parse_files_from_response()
# ---------------------------------------------------------------------------

class TestParseFilesFromResponse:
    def test_parses_single_file(self):
        agent, _ = _make_agent()
        response = "FILE: src/main.py\n```python\nprint('hello')\n```"
        files = agent.parse_files_from_response(response)
        assert "src/main.py" in files
        assert "print('hello')" in files["src/main.py"]

    def test_parses_multiple_files(self):
        agent, _ = _make_agent()
        response = (
            "FILE: a.py\n```python\nx=1\n```\n"
            "FILE: b.py\n```python\ny=2\n```"
        )
        files = agent.parse_files_from_response(response)
        assert len(files) == 2

    def test_returns_empty_dict_when_no_files(self):
        agent, _ = _make_agent()
        assert agent.parse_files_from_response("No changes needed.") == {}
