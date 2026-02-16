"""
Autonomous Agent
================

Main orchestrator for autonomous software development.
"""

import os
import re
from pathlib import Path
from typing import Optional

from coding_tool import CodingTool, OpenCodeCodingTool
from task_manager import TaskManager
from executor import Executor
from git_manager import GitManager
from refiner import TaskRefiner
from task import SubTask


class AutonomousAgent:
    """Autonomous software development agent."""
    
    def __init__(self, requirement: Optional[str], project_dir: Path, coding_tool: CodingTool):
        self.requirement = requirement
        self.project_dir = project_dir
        self.coding_tool = coding_tool
        self.task_manager = TaskManager(project_dir)
        self.executor = Executor(str(project_dir))
        self.git_manager = GitManager(str(project_dir))
        self.refiner = TaskRefiner(self.coding_tool)
    
    def parse_files_from_response(self, response: str) -> dict:
        """
        Parse file changes from AI response.
        
        Args:
            response: AI response text
            
        Returns:
            Dictionary mapping file paths to content
        """
        files = {}
        pattern = r"FILE:\s*(.*?)\n```(?:\w+)?\n(.*?)\n```"
        matches = re.findall(pattern, response, re.DOTALL)
        for path, content in matches:
            path = path.strip()
            path_obj = Path(path)
            if path_obj.is_absolute():
                try:
                    path_obj = path_obj.relative_to(self.project_dir)
                except ValueError:
                    path_obj = Path(path_obj.name)
            files[str(path_obj)] = content
        return files
    
    def get_file_context(self) -> str:
        """
        Get current codebase context.
        
        Returns:
            String containing all file contents
        """
        file_context = ""
        for root, dirs, files in os.walk(self.project_dir):
            if ".git" in dirs:
                dirs.remove(".git")
            if "node_modules" in dirs:
                dirs.remove("node_modules")
            if "__pycache__" in dirs:
                dirs.remove("__pycache__")
                
            for file in files:
                if file in ["tasks.json", "requirements.txt", ".env"]:
                    continue
                rel_path = os.path.relpath(os.path.join(root, file), self.project_dir)
                try:
                    with open(os.path.join(root, file), "r") as f:
                        content = f.read()
                        file_context += f"\nFILE: {rel_path}\n---\n{content}\n---\n"
                except Exception:
                    pass
        return file_context
    
    def plan(self):
        """Plan tasks from the requirement."""
        if not self.requirement:
            return
        
        print(f"Planning tasks for: {self.requirement}")
        try:
            planner_prompt = """You are a senior software architect. Your task is to take a high-level user requirement and break it down into a list of small, incremental, and testable subtasks.

IMPORTANT: Task IDs must follow a hierarchical format using strings:
- First-level tasks use simple numeric IDs: "1", "2", "3", ...
- If a task needs to be broken down into subtasks, use "-" to connect the original ID with the subtask ID:
  - Task "1" broken into 3 subtasks → "1-1", "1-2", "1-3"
  - Task "1-1" broken into 2 subtasks → "1-1-1", "1-1-2"
- Task IDs must always be unique strings

Output the result in the following JSON format:
{
  "tasks": [
    {
      "id": "1",
      "title": "Short title",
      "description": "Detailed description of what to do",
      "test_command": "The shell command to run to verify this subtask"
    }
  ]
}
"""
            plan_response = self.coding_tool.query_json(
                f"Requirement: {self.requirement}",
                system_instruction=planner_prompt
            )
            self.task_manager.set_tasks(plan_response["tasks"], requirement=self.requirement)
            print(f"\nPlanned {len(self.task_manager.tasks)} tasks:")
            for task in self.task_manager.tasks:
                print(f"  {task.id}. {task.title}")
        except Exception as e:
            print(f"Failed to plan tasks: {e}")
            raise
    
    def run(self, max_tasks: Optional[int] = None, timeout: Optional[int] = None):
        """
        Execute tasks until completion or max_tasks limit.
        
        Args:
            max_tasks: Maximum number of tasks to execute
            timeout: Timeout for each AI query in seconds
        """
        import json
        
        total_tasks = len(self.task_manager.tasks)
        completed_tasks = sum(1 for t in self.task_manager.tasks if t.status == "completed")
        task_count = 0
        
        while True:
            if max_tasks is not None and task_count >= max_tasks:
                print(f"\nReached maximum task limit: {max_tasks}")
                break
                
            task = self.task_manager.get_next_task()
            if not task:
                if total_tasks > 0:
                    print("\nAll tasks completed!")
                break
            
            try:
                print(f"\n--- Processing Task [{task.id}/{total_tasks}]: {task.title} ---")
                self.task_manager.update_task_status(task.id, "in_progress")
                
                file_context = self.get_file_context()
                context = f"Subtask: {task.description}\nTest Command: {task.test_command}\n"
                context += f"\nCurrent codebase:\n{file_context}\n"
                
                coder_prompt = """You are an expert software engineer. Your task is to implement a specific subtask in a codebase.

Provide a list of files to be created or modified, with their FULL content.
IMPORTANT: All file paths must be RELATIVE to the project directory. Do NOT use absolute paths.
Format:
FILE: path/to/file
```
content
```
FILE: path/to/another_file
```
content
```
"""
                
                print("Coding tool is coding...")
                coder_response = None
                try:
                    coder_response = self.coding_tool.query(
                        context,
                        system_instruction=coder_prompt,
                        timeout=timeout
                    )
                except TimeoutError as e:
                    print(f"Task timed out: {e}")
                    print("Attempting to break down task into smaller subtasks...")
                    
                    self.task_manager.update_task_status(task.id, "failed")
                    
                    try:
                        breakdown_context = f"The following task timed out after {timeout} seconds:\n\nTask ID: {task.id}\nTitle: {task.title}\nDescription: {task.description}\n\nPlease break this task down into 2-3 smaller, more manageable subtasks. For each subtask, provide:\n- id (increment from original task ID with hyphens, e.g., {task.id}-1, {task.id}-2)\n- title\n- description\n- test_command\n- status: 'pending'\n\nReturn ONLY a JSON object with a 'tasks' array containing the new subtasks."
                        
                        breakdown_response = self.coding_tool.query_json(
                            breakdown_context,
                            system_instruction="You are a task breakdown specialist. Return only valid JSON.",
                            timeout=120
                        )
                        
                        if "tasks" in breakdown_response:
                            new_tasks = breakdown_response["tasks"]
                            for new_task in new_tasks:
                                self.task_manager.add_task(SubTask(**new_task))
                            print(f"Created {len(new_tasks)} subtasks from timed-out task.")
                            task_count += 1
                            continue
                    except Exception as breakdown_error:
                        print(f"Failed to break down task: {breakdown_error}")
                    
                    task_count += 1
                    continue
                
                if coder_response is None:
                    print("No response from coding tool. Skipping task.")
                    self.task_manager.update_task_status(task.id, "failed")
                    task_count += 1
                    continue
                
                files_to_write = self.parse_files_from_response(coder_response)
                if files_to_write:
                    for path, content in files_to_write.items():
                        full_path = self.project_dir / path
                        full_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(full_path, "w") as f:
                            f.write(content)
                        print(f"Wrote {path}")
                else:
                    print("No file changes provided.")
                
                print("Running tests...")
                exit_code, output = self.executor.run_command(task.test_command)
                result_context = f"Task '{task.title}' " + ("passed" if exit_code == 0 else "failed")
                result_context += f"\nOutput:\n{output}"
                
                error_patterns = ['error', 'Error', 'ERROR', 'failed', 'Failed', 'FAILED', 'exception', 'Exception', 'EXCEPTION']
                has_error = any(pattern in output for pattern in error_patterns)
                
                if has_error and exit_code == 0:
                    print("Warning: Output contains error patterns despite exit code 0")
                
                if exit_code == 0 and not has_error:
                    print("Tests passed!")
                    self.task_manager.update_task_status(task.id, "completed")
                    
                    diff = self.git_manager.get_diff()
                    untracked = self.git_manager.get_untracked_files()
                    if untracked:
                        diff += f"\nUntracked files: {', '.join(untracked)}"
                    
                    commit_msg_prompt = """You are a senior developer who writes excellent commit messages.
Generate a full commit message for the changes just made.
The message should include:
1. A concise subject line.
2. A body explaining:
   - WHAT was done.
   - WHY it was done.
   - HOW this subtask contributes to the overall goal.
Use the following context:
Subtask: {subtask_description}
Diff: {diff}
"""
                    commit_msg = self.coding_tool.query(commit_msg_prompt.format(
                        subtask_description=task.description,
                        diff=diff
                    ))
                    self.git_manager.commit(commit_msg)
                    print("Changes committed.")
                else:
                    print("Tests failed.")
                    self.task_manager.update_task_status(task.id, "failed")
                
                print("Refining task list...")
                current_tasks_dict = [t.model_dump() for t in self.task_manager.tasks]
                updated_tasks = self.refiner.refine(
                    requirement=self.task_manager.requirement,
                    tasks=current_tasks_dict,
                    last_coder_response=coder_response,
                    last_result=result_context,
                    file_context=file_context,
                    exit_code=exit_code,
                    last_task_id=task.id
                )
                
                old_tasks_repr = json.dumps(current_tasks_dict, sort_keys=True)
                new_tasks_repr = json.dumps(updated_tasks, sort_keys=True)
                
                if old_tasks_repr != new_tasks_repr:
                    self.task_manager.set_tasks(updated_tasks)
                    new_total = len(self.task_manager.tasks)
                    print(f"Task list updated. Total tasks: {new_total}")
                    total_tasks = new_total
                
                if exit_code != 0:
                    next_task = self.task_manager.get_next_task()
                    if not next_task:
                        print("No pending tasks after failure. Stopping.")
                        break
                    print(f"Next task after failure: {next_task.title}")
                
            except Exception as e:
                print(f"An unexpected error occurred while processing task: {e}")
                self.task_manager.update_task_status(task.id, "failed")
            
            task_count += 1


def autonomous_coding(
    requirement: str,
    project_dir: str,
    recover: bool = False,
    max_tasks: Optional[int] = None
):
    """
    Fully autonomous software development from requirement to completion.
    
    Args:
        requirement: High-level requirement description
        project_dir: Target project directory
        recover: Whether to skip planning and recover from crash
        max_tasks: Maximum number of tasks to execute
    """
    project_path = Path(project_dir).resolve()
    coding_tool = OpenCodeCodingTool()
    
    agent = AutonomousAgent(
        requirement=requirement,
        project_dir=project_path,
        coding_tool=coding_tool
    )
    
    if requirement and not recover:
        agent.plan()
    
    if max_tasks:
        agent.run(max_tasks=max_tasks, timeout=300)
    else:
        agent.run(timeout=300)
