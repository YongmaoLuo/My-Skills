"""
Task Refiner
============

Analyzes task execution results and refines the task list.
"""

import json
from typing import List, Dict, Optional

from coding_tool import CodingTool
from config import AgentConfig
from config_registry import ConfigRegistry


class TaskRefiner:
    """Refines task list based on execution results."""

    def __init__(self, coding_tool: CodingTool, config: Optional[AgentConfig] = None):
        self.coding_tool = coding_tool
        self.config = config or ConfigRegistry.get('coding')

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

        # Get the refiner prompt from config
        refiner_prompt = self.config.refiner_system_prompt

        # Add domain knowledge if available
        if self.config.domain_knowledge:
            refiner_prompt = f"{self.config.domain_knowledge}\n\n{refiner_prompt}"

        try:
            response = self.coding_tool.query_json(refine_context, system_instruction=refiner_prompt)
            new_tasks = response.get("tasks", tasks)

            # Preserve metadata from existing tasks
            existing_tasks_map = {task.get("id"): task for task in tasks}
            for new_task in new_tasks:
                task_id = new_task.get("id")
                if task_id in existing_tasks_map:
                    existing_task = existing_tasks_map[task_id]
                    # Preserve updated_time
                    if "updated_time" in existing_task and "updated_time" not in new_task:
                        new_task["updated_time"] = existing_task["updated_time"]
                    # Preserve completed status
                    if existing_task["status"] == "completed":
                        new_task["status"] = "completed"

            return new_tasks
        except Exception as e:
            print(f"Error during refinement: {e}")
            return tasks
