"""
Configuration Registry
======================

Registry for domain-specific configurations.
"""

from typing import Dict, Optional
from config import AgentConfig


class ConfigRegistry:
    """Registry for domain-specific configurations."""

    _configs: Dict[str, AgentConfig] = {}

    @classmethod
    def register(cls, name: str, config: AgentConfig):
        """
        Register a configuration with a given name.

        Args:
            name: Configuration name
            config: AgentConfig instance
        """
        cls._configs[name] = config

    @classmethod
    def get(cls, name: str) -> Optional[AgentConfig]:
        """
        Get a configuration by name.

        Args:
            name: Configuration name

        Returns:
            AgentConfig instance or None if not found
        """
        return cls._configs.get(name)

    @classmethod
    def list_configs(cls) -> list:
        """
        List all registered configuration names.

        Returns:
            List of configuration names
        """
        return list(cls._configs.keys())

    @classmethod
    def clear(cls):
        """Clear all registered configurations."""
        cls._configs.clear()


# Register default coding configuration
DEFAULT_CODING_CONFIG = AgentConfig(
    planner_system_prompt="""You are a senior software architect. Your task is to take a high-level user requirement and break it down into a list of small, incremental, and testable subtasks.

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
""",
    executor_system_prompt="""You are an expert software engineer. Your task is to implement a specific subtask in a codebase.

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
""",
    refiner_system_prompt="""You are a senior software architect. Your task is to review the progress of a project and update the task list based on the result of the most recent subtask.

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
""",
    domain_knowledge="",
    file_patterns=["*.py", "*.js", "*.ts", "*.tsx", "*.java", "*.go", "*.rs", "*.c", "*.cpp", "*.h"],
    max_retries=5,
    background_task_timeout=180
)

# Register the default config
ConfigRegistry.register("coding", DEFAULT_CODING_CONFIG)
