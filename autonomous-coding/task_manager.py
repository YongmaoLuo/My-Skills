"""
Task Manager
=============

Manages task state, persistence, and lifecycle.
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from task import SubTask


class TaskManager:
    """Manages task state and persistence."""

    def __init__(self, project_dir: Path):
        self.tasks_file = project_dir / "tasks.json"
        self.tasks: List[SubTask] = []
        self.requirement: str = ""
        self.stop_reason: Optional[str] = None
        self.reason_detail: Optional[str] = None
        self.load_tasks()
    
    def load_tasks(self):
        """Load tasks from tasks.json file."""
        if not self.tasks_file.exists():
            return

        with open(self.tasks_file, "r") as f:
            data = json.load(f)

        _TASK_FIELDS = {"id", "title", "description", "test_command", "status",
                        "updated_time", "failure_reason"}

        def _make_task(t: dict) -> SubTask:
            task_dict = {k: v for k, v in t.items() if k in _TASK_FIELDS}
            task_dict.setdefault("updated_time", None)
            task_dict.setdefault("failure_reason", None)
            return SubTask(**task_dict)

        if isinstance(data, dict):
            self.tasks = [_make_task(t) for t in data.get("tasks", [])]
            self.requirement = data.get("requirement", "")
            self.stop_reason = data.get("stop_reason", None)
            self.reason_detail = data.get("reason_detail", None)
        else:
            self.tasks = [_make_task(t) for t in data]
    
    def save_tasks(self):
        """Save tasks to tasks.json file."""
        with open(self.tasks_file, "w") as f:
            tasks_data = []
            for task in self.tasks:
                task_dict = task.model_dump(exclude_none=False)
                if "updated_time" not in task_dict:
                    task_dict["updated_time"] = None
                tasks_data.append(task_dict)
            json.dump({
                "requirement": self.requirement,
                "stop_reason": self.stop_reason,
                "reason_detail": self.reason_detail,
                "tasks": tasks_data
            }, f, indent=2)
    
    def set_tasks(self, tasks: List[Dict], requirement: Optional[str] = None):
        """
        Set new tasks, preserving metadata from existing tasks.
        
        Args:
            tasks: List of task dictionaries
            requirement: Optional requirement string
        """
        new_tasks = []
        existing_tasks_map = {t.id: t for t in self.tasks}
        
        for new_task_dict in tasks:
            task_id = new_task_dict.get("id")
            
            if task_id in existing_tasks_map:
                existing_task = existing_tasks_map[task_id]
                if "updated_time" not in new_task_dict:
                    new_task_dict["updated_time"] = existing_task.updated_time
            elif "updated_time" not in new_task_dict:
                new_task_dict["updated_time"] = None
            
            new_tasks.append(SubTask(**new_task_dict))
        
        self.tasks = new_tasks
        if requirement:
            self.requirement = requirement
        self.save_tasks()
    
    def get_next_task(self) -> Optional[SubTask]:
        """
        Get the next task to process.

        Returns:
            Next pending/in_progress task, or None if all are completed/failed
        """
        for task in self.tasks:
            if task.status in ["pending", "in_progress"]:
                return task
        return None

    def find_completed_duplicate(self, task: SubTask) -> Optional[SubTask]:
        """
        Find a completed task with the same title as the given task.

        A match means the system already applied this fix but the problem recurred,
        indicating a circular loop the agent cannot resolve on its own.

        Args:
            task: The task about to be executed

        Returns:
            The matching completed task, or None if no duplicate found
        """
        for t in self.tasks:
            if t.id != task.id and t.status == "completed" and t.title == task.title:
                return t
        return None

    def update_task_status(self, task_id: str, status: str):
        """
        Update task status and timestamp.

        Args:
            task_id: Task ID to update
            status: New status value
        """
        for task in self.tasks:
            if task.id == task_id:
                task.status = status
                task.updated_time = datetime.utcnow().isoformat()
                break
        self.save_tasks()

    def record_task_failure(self, task_id: str, error: str):
        """
        Mark a task as failed and record the failure reason.

        Args:
            task_id: Task ID to mark as failed
            error: Error message to record as failure_reason
        """
        for task in self.tasks:
            if task.id == task_id:
                task.status = "failed"
                task.failure_reason = error[:1000]
                task.updated_time = datetime.utcnow().isoformat()
                break
        self.save_tasks()
    
    def set_stop_reason(self, reason: str, detail: Optional[str] = None):
        """
        Record why the run stopped, persisted as top-level fields in tasks.json.

        Args:
            reason: One of 'success' or 'repeated_failure'
            detail: Human-readable description of the specific stopping cause
        """
        self.stop_reason = reason
        self.reason_detail = detail
        self.save_tasks()

    def add_task(self, task: SubTask):
        """
        Add a new task.
        
        Args:
            task: SubTask to add
        """
        if not task.updated_time:
            task.updated_time = datetime.utcnow().isoformat()
        self.tasks.append(task)
        self.save_tasks()
