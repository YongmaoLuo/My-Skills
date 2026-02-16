"""
Task Refiner
============

Analyzes task execution results and refines the task list.
"""

import json
from typing import List, Dict, Optional

from coding_tool import CodingTool


class TaskRefiner:
    """Refines task list based on execution results."""
    
    def __init__(self, coding_tool: CodingTool):
        self.coding_tool = coding_tool
    
    def refine(
        self,
        requirement: str,
        tasks: List[Dict],
        last_coder_response: str,
        last_result: str,
        file_context: str,
        exit_code: int,
        last_task_id: Optional[str] = None
    ) -> List[Dict]:
        """
        Refine task list based on last execution result.
        
        Args:
            requirement: Original project requirement
            tasks: Current list of tasks
            last_coder_response: Last AI implementation attempt
            last_result: Test execution result
            file_context: Current codebase state
            exit_code: Exit code from test command
            last_task_id: ID of the last executed task
            
        Returns:
            Updated list of tasks
        """
        refine_context = f"Requirement: {requirement}\n"
        refine_context += f"Last Task ID: {last_task_id or 'N/A'}\n"
        refine_context += f"Last Task Implementation Attempt:\n{last_coder_response}\n"
        refine_context += f"Last Task Result: {last_result}\n"
        refine_context += f"Current Tasks: {json.dumps(tasks, indent=2)}\n"
        refine_context += f"Current Codebase:\n{file_context}"
        
        if exit_code != 0:
            refine_context += "\n\nCRITICAL INSTRUCTION: The last task FAILED. You must NOT leave the task list as is. You MUST break down the failed task into smaller, simpler subtasks to resolve the error. Do not just retry the same task."
            if last_task_id:
                refine_context += f"\n\nThe failed task ID is '{last_task_id}'. When breaking it down into subtasks, use hierarchical IDs like '{last_task_id}-1', '{last_task_id}-2', etc."
        
        refiner_prompt = """You are a senior software architect. Your task is to review the progress of a project and update the task list based on the result of the most recent subtask.

IMPORTANT: Task IDs must follow a hierarchical format using strings:
- First-level tasks use simple numeric IDs: "1", "2", "3", ...
- If a task needs to be broken down into subtasks, use "-" to connect the original ID with the subtask ID:
  - Task "1" broken into 3 subtasks → "1-1", "1-2", "1-3"
  - Task "1-1" broken into 2 subtasks → "1-1-1", "1-1-2"
- Task IDs must always be unique strings

Your goal is to ensure the task list remains accurate and efficient.

CRITICAL: If the last task FAILED, you MUST:
1. Analyze the error output and the implementation attempt to understand the root cause.
2. Break down the failed task into smaller, more manageable, and more specific subtasks that address the root cause of the failure.
3. Generate hierarchical IDs for the new subtasks. For example, if task "2" failed, create subtasks like "2-1", "2-2", "2-3".
4. Replace the failed task with the new subtasks.

Output the COMPLETE updated list of tasks in the following JSON format:
{
  "tasks": [
    {
      "id": "1",
      "title": "Short title",
      "description": "Detailed description",
      "test_command": "Command to verify",
      "status": "pending/completed/failed/in_progress",
      "updated_time": "ISO8601 timestamp or null"
    }
  ]
}
IMPORTANT: You MUST preserve these metadata fields from existing tasks:
1. "status" - Do not change the status of completed tasks
2. "updated_time" - Always preserve this field if it exists
When returning the updated task list, include these fields for all existing tasks.
"""
        
        try:
            response = self.coding_tool.query_json(refine_context, system_instruction=refiner_prompt)
            new_tasks = response.get("tasks", tasks)
            
            existing_tasks_map = {task.get("id"): task for task in tasks}
            
            for new_task in new_tasks:
                task_id = new_task.get("id")
                if task_id in existing_tasks_map:
                    existing_task = existing_tasks_map[task_id]
                    if "updated_time" in existing_task and "updated_time" not in new_task:
                        new_task["updated_time"] = existing_task["updated_time"]
                    if existing_task["status"] == "completed":
                        new_task["status"] = "completed"
            
            return new_tasks
        except Exception as e:
            print(f"Error during refinement: {e}")
            return tasks
