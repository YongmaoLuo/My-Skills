"""Unit tests for TaskManager."""

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from task import SubTask
from task_manager import TaskManager


def _make_manager(tasks_data=None, requirement="test req") -> tuple:
    """Return (tmp_dir, TaskManager) with optional pre-seeded tasks.json."""
    tmp = tempfile.mkdtemp()
    path = Path(tmp)
    if tasks_data is not None:
        with open(path / "tasks.json", "w") as f:
            json.dump({"requirement": requirement, "tasks": tasks_data}, f)
    tm = TaskManager(path)
    return path, tm


def _task_dict(id="1", title="T", description="D", test_cmd="echo ok",
               status="pending", error_count=0, last_error=None, failure_reason=None):
    return {
        "id": id, "title": title, "description": description,
        "test_command": test_cmd, "status": status,
        "error_count": error_count, "last_error": last_error,
        "failure_reason": failure_reason, "updated_time": None
    }


class TestTaskManagerLoad:
    def test_empty_when_no_file(self):
        _, tm = _make_manager()
        assert tm.tasks == []
        assert tm.requirement == ""

    def test_loads_requirement(self):
        _, tm = _make_manager([_task_dict()], requirement="Build app")
        assert tm.requirement == "Build app"

    def test_loads_tasks(self):
        _, tm = _make_manager([_task_dict(id="1"), _task_dict(id="2")])
        assert len(tm.tasks) == 2
        assert tm.tasks[0].id == "1"
        assert tm.tasks[1].id == "2"

    def test_defaults_missing_fields_on_load(self):
        # tasks.json without new fields (legacy format)
        tmp = tempfile.mkdtemp()
        path = Path(tmp)
        legacy = [{"id": "1", "title": "T", "description": "D",
                   "test_command": "echo ok", "status": "pending"}]
        with open(path / "tasks.json", "w") as f:
            json.dump({"requirement": "r", "tasks": legacy}, f)
        tm = TaskManager(path)
        assert tm.tasks[0].error_count == 0
        assert tm.tasks[0].last_error is None
        assert tm.tasks[0].failure_reason is None

    def test_loads_list_format(self):
        """Backwards-compat: tasks.json is a plain list."""
        tmp = tempfile.mkdtemp()
        path = Path(tmp)
        with open(path / "tasks.json", "w") as f:
            json.dump([_task_dict(id="1")], f)
        tm = TaskManager(path)
        assert len(tm.tasks) == 1


class TestTaskManagerSave:
    def test_save_and_reload(self):
        path, tm = _make_manager()
        tm.set_tasks([_task_dict(id="1", status="completed")], requirement="req1")
        tm2 = TaskManager(path)
        assert len(tm2.tasks) == 1
        assert tm2.tasks[0].status == "completed"
        assert tm2.requirement == "req1"

    def test_save_preserves_error_count(self):
        path, tm = _make_manager([_task_dict(id="1")])
        tm.tasks[0].error_count = 2
        tm.save_tasks()
        tm2 = TaskManager(path)
        assert tm2.tasks[0].error_count == 2


class TestGetNextTask:
    def test_returns_pending_task(self):
        _, tm = _make_manager([_task_dict(id="1", status="pending")])
        task = tm.get_next_task()
        assert task is not None
        assert task.id == "1"

    def test_returns_in_progress_task(self):
        _, tm = _make_manager([_task_dict(id="1", status="in_progress")])
        task = tm.get_next_task()
        assert task is not None

    def test_skips_completed_task(self):
        _, tm = _make_manager([_task_dict(id="1", status="completed")])
        assert tm.get_next_task() is None

    def test_skips_fatal_task(self):
        _, tm = _make_manager([_task_dict(id="1", status="fatal")])
        assert tm.get_next_task() is None

    def test_returns_none_when_all_done(self):
        data = [_task_dict(id=str(i), status="completed") for i in range(3)]
        _, tm = _make_manager(data)
        assert tm.get_next_task() is None

    def test_returns_first_pending_among_mixed(self):
        data = [
            _task_dict(id="1", status="completed"),
            _task_dict(id="2", status="pending"),
            _task_dict(id="3", status="pending"),
        ]
        _, tm = _make_manager(data)
        assert tm.get_next_task().id == "2"


class TestUpdateTaskStatus:
    def test_updates_status(self):
        _, tm = _make_manager([_task_dict(id="1", status="pending")])
        tm.update_task_status("1", "completed")
        assert tm.tasks[0].status == "completed"

    def test_sets_updated_time(self):
        _, tm = _make_manager([_task_dict(id="1")])
        assert tm.tasks[0].updated_time is None
        tm.update_task_status("1", "in_progress")
        assert tm.tasks[0].updated_time is not None

    def test_persists_to_file(self):
        path, tm = _make_manager([_task_dict(id="1")])
        tm.update_task_status("1", "completed")
        tm2 = TaskManager(path)
        assert tm2.tasks[0].status == "completed"


class TestRecordTaskError:
    def test_increments_error_count(self):
        _, tm = _make_manager([_task_dict(id="1")])
        tm.record_task_error("1", "some error")
        assert tm.tasks[0].error_count == 1
        assert tm.tasks[0].last_error == "some error"

    def test_returns_false_below_threshold(self):
        _, tm = _make_manager([_task_dict(id="1")])
        result = tm.record_task_error("1", "err")
        assert result is False
        assert tm.tasks[0].status == "pending"

    def test_returns_true_at_threshold(self):
        _, tm = _make_manager([_task_dict(id="1", error_count=2)])
        result = tm.record_task_error("1", "err again")
        assert result is True

    def test_sets_fatal_status_at_threshold(self):
        _, tm = _make_manager([_task_dict(id="1", error_count=2)])
        tm.record_task_error("1", "final error")
        assert tm.tasks[0].status == "fatal"

    def test_sets_failure_reason_at_threshold(self):
        _, tm = _make_manager([_task_dict(id="1", error_count=2)])
        tm.record_task_error("1", "final error")
        assert tm.tasks[0].failure_reason is not None
        assert "final error" in tm.tasks[0].failure_reason

    def test_fatal_persists_to_file(self):
        path, tm = _make_manager([_task_dict(id="1", error_count=2)])
        tm.record_task_error("1", "kaboom")
        tm2 = TaskManager(path)
        assert tm2.tasks[0].status == "fatal"
        assert tm2.tasks[0].failure_reason is not None

    def test_truncates_long_error(self):
        _, tm = _make_manager([_task_dict(id="1")])
        long_error = "x" * 2000
        tm.record_task_error("1", long_error)
        assert len(tm.tasks[0].last_error) <= 1000


class TestSetTasks:
    def test_replaces_tasks(self):
        _, tm = _make_manager([_task_dict(id="1")])
        tm.set_tasks([_task_dict(id="2")])
        assert len(tm.tasks) == 1
        assert tm.tasks[0].id == "2"

    def test_preserves_updated_time_for_existing(self):
        _, tm = _make_manager([_task_dict(id="1")])
        tm.update_task_status("1", "in_progress")
        saved_time = tm.tasks[0].updated_time
        # Omit updated_time so set_tasks can preserve the existing value
        new_dict = {"id": "1", "title": "T", "description": "D",
                    "test_command": "echo ok", "status": "pending"}
        tm.set_tasks([new_dict])
        assert tm.tasks[0].updated_time == saved_time

    def test_sets_requirement(self):
        _, tm = _make_manager()
        tm.set_tasks([_task_dict(id="1")], requirement="new req")
        assert tm.requirement == "new req"


class TestAddTask:
    def test_appends_task(self):
        _, tm = _make_manager([_task_dict(id="1")])
        new_task = SubTask(id="2", title="T2", description="D2", test_command="echo 2")
        tm.add_task(new_task)
        assert len(tm.tasks) == 2
        assert tm.tasks[1].id == "2"

    def test_sets_updated_time(self):
        _, tm = _make_manager()
        task = SubTask(id="1", title="T", description="D", test_command="echo ok")
        tm.add_task(task)
        assert tm.tasks[0].updated_time is not None
