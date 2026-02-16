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
        self.load_tasks()
    
    def load_tasks(self):
        """Load tasks from tasks.json file."""
        if not self.tasks_file.exists():
            return
        
        with open(self.tasks_file, "r") as f:
            data = json.load(f)
            
            if isinstance(data, dict):
                tasks_data = data.get("tasks", [])
                self.tasks = []
                for t in tasks_data:
                    task_dict = t.copy()
                    if "updated_time" not in task_dict:
                        task_dict["updated_time"] = None
                    self.tasks.append(SubTask(**task_dict))
                self.requirement = data.get("requirement", "")
            else:
                self.tasks = []
                for t in data:
                    task_dict = t.copy()
                    if "updated_time" not in task_dict:
                        task_dict["updated_time"] = None
                    self.tasks.append(SubTask(**task_dict))
    
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
            Next task or None if all tasks are completed
        """
        for task in self.tasks:
            if task.status in ["pending", "failed", "in_progress"]:
                return task
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
