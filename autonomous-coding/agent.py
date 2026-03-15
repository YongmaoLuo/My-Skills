"""
Autonomous Agent
================

Main orchestrator for autonomous software development.
"""

import os
import re
import json
from pathlib import Path
from typing import Optional, List

from coding_tool import CodingTool, OpenCodeCodingTool, ClaudeCodingTool
from task_manager import TaskManager
from executor import Executor
from git_manager import GitManager
from refiner import TaskRefiner
from task import SubTask
from config import AgentConfig
from config_registry import ConfigRegistry
from retry_manager import RetryManager
from background_manager import BackgroundManager
from rollback_manager import RollbackManager


class FatalTaskError(Exception):
    """Raised when a task has failed too many times and requires human intervention."""

    def __init__(self, task_id: str, reason: str):
        self.task_id = task_id
        self.reason = reason
        super().__init__(f"Task [{task_id}] fatally failed: {reason}")


class AutonomousAgent:
    """Configurable autonomous agent for various task types."""

    def __init__(
        self,
        requirement: Optional[str],
        project_dir: Path,
        coding_tool: CodingTool,
        config: Optional[AgentConfig] = None
    ):
        self.requirement = requirement
        self.project_dir = project_dir
        self.coding_tool = coding_tool
        self.config = config or ConfigRegistry.get('coding')

        # Initialize managers
        self.task_manager = TaskManager(project_dir)
        self.background_manager = BackgroundManager()
        self.executor = Executor(str(project_dir), self.background_manager)
        self.git_manager = GitManager(str(project_dir))
        self.retry_manager = RetryManager()
        self.rollback_manager = RollbackManager(str(project_dir))
        self.refiner = TaskRefiner(self.coding_tool, self.config)

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
        Get current codebase context filtered by domain patterns.

        Returns:
            String containing all file contents
        """
        file_context = ""
        exclude_dirs = {".git", "node_modules", "__pycache__", ".venv", "venv", "build", "dist"}
        exclude_files = {"tasks.json", "requirements.txt", ".env", "tasks.lock"}

        for root, dirs, files in os.walk(self.project_dir):
            # Filter directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]

            for file in files:
                if file in exclude_files:
                    continue

                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, self.project_dir)

                # Check if file matches domain patterns
                if self._should_include_file(file_path, rel_path):
                    try:
                        with open(file_path, "r", encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            file_context += f"\nFILE: {rel_path}\n---\n{content}\n---\n"
                    except Exception:
                        pass
        return file_context

    def _should_include_file(self, file_path: str, rel_path: str) -> bool:
        """
        Check if file should be included based on domain patterns.

        Args:
            file_path: Full file path
            rel_path: Relative path from project root

        Returns:
            True if file should be included
        """
        import fnmatch

        if not self.config or not self.config.file_patterns:
            return True

        for pattern in self.config.file_patterns:
            if fnmatch.fnmatch(rel_path, pattern):
                return True
            if fnmatch.fnmatch(os.path.basename(file_path), pattern):
                return True
        return False

    def plan(self):
        """Plan tasks from the requirement using domain-specific configuration."""
        if not self.requirement:
            return

        print(f"Planning tasks for: {self.requirement}")
        try:
            # Use config's planner prompt or default
            planner_prompt = self.config.planner_system_prompt

            # Add domain knowledge if available
            full_prompt = ""
            if self.config.domain_knowledge:
                full_prompt = f"{self.config.domain_knowledge}\n\n"

            full_prompt += f"Requirement: {self.requirement}"

            plan_response = self.coding_tool.query_json(
                full_prompt,
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

            # Execute task with retry mechanism
            try:
                success = self._execute_task_with_retry(task, max_retries=self.config.max_retries, timeout=timeout)
            except FatalTaskError as e:
                print(f"\n{'=' * 60}")
                print(f"AUTONOMOUS CODING STOPPED — HUMAN INTERVENTION REQUIRED")
                print(f"{'=' * 60}")
                print(f"Task [{e.task_id}] has failed {self.task_manager.MAX_TASK_ERRORS} times "
                      f"and the system cannot resolve it automatically.")
                print(f"\nReason recorded in tasks.json:")
                print(f"  {e.reason}")
                print(f"\nPlease inspect tasks.json for the full failure context,")
                print(f"fix the underlying issue, and re-run with --recover.")
                print(f"{'=' * 60}\n")
                break
            task_count += 1

            # Update total tasks count after potential refinement
            total_tasks = len(self.task_manager.tasks)

    def _execute_task_with_retry(self, task: SubTask, max_retries: int = 5, timeout: Optional[int] = None) -> bool:
        """
        Execute a task with retry mechanism.

        Args:
            task: Task to execute
            max_retries: Maximum number of retry attempts per run
            timeout: Timeout for AI queries

        Returns:
            True if task completed successfully, False if it failed.
            Raises FatalTaskError if the task has persistently failed MAX_TASK_ERRORS times.
        """
        for attempt in range(max_retries):
            try:
                print(f"\n--- Processing Task [{task.id}] (Attempt {attempt + 1}/{max_retries}, "
                      f"total errors: {task.error_count}): {task.title} ---")
                self.task_manager.update_task_status(task.id, "in_progress")

                # Get context and add retry modifier if this is a retry
                file_context = self.get_file_context()
                context = f"Subtask: {task.description}\nTest Command: {task.test_command}\n"
                context += f"\nCurrent codebase:\n{file_context}\n"

                # Add retry context if this is a retry attempt (in-run or cross-run)
                if attempt > 0 or task.error_count > 0:
                    retry_modifier = self.retry_manager.get_retry_prompt_modifier(task.id)
                    if task.last_error and not retry_modifier:
                        retry_modifier = (
                            f"\n\n[PREVIOUS RUN ERROR]\nThis task failed in a previous run with:\n"
                            f"{task.last_error}\nPlease try a different approach."
                        )
                    context += retry_modifier

                # Use config's executor prompt
                coder_prompt = self.config.executor_system_prompt

                print("Coding tool is coding...")
                coder_response = None

                # Determine if we should use background execution
                previous_timeout = self.executor.had_previous_timeout(task.id)

                try:
                    if previous_timeout:
                        print("Previous timeout detected, using background execution...")
                        coder_response = self.coding_tool.query(
                            context,
                            system_instruction=coder_prompt,
                            timeout=None  # No timeout for background
                        )
                    else:
                        coder_response = self.coding_tool.query(
                            context,
                            system_instruction=coder_prompt,
                            timeout=timeout
                        )
                except TimeoutError as e:
                    print(f"Task timed out: {e}")
                    self.executor.record_timeout(task.id, timeout or 300)
                    self.retry_manager.record_attempt(task.id, str(e), False)
                    error_msg = str(e)

                    if attempt < max_retries - 1:
                        print("Retrying...")
                        continue

                    print("Max retries reached after timeouts, breaking down task...")
                    self._breakdown_failed_task(task, error_msg)
                    fatal = self.task_manager.record_task_error(task.id, error_msg)
                    if fatal:
                        raise FatalTaskError(task.id, task.failure_reason or error_msg)
                    return False

                if coder_response is None:
                    print("No response from coding tool.")
                    error_msg = "No response from coding tool"
                    self.retry_manager.record_attempt(task.id, error_msg, False)
                    if attempt < max_retries - 1:
                        continue
                    fatal = self.task_manager.record_task_error(task.id, error_msg)
                    if fatal:
                        raise FatalTaskError(task.id, task.failure_reason or error_msg)
                    return False

                # Apply file changes
                files_to_write = self.parse_files_from_response(coder_response)
                changed_files = []
                if files_to_write:
                    for path, content in files_to_write.items():
                        full_path = self.project_dir / path
                        full_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(full_path, "w") as f:
                            f.write(content)
                        changed_files.append(path)
                        print(f"Wrote {path}")
                else:
                    print("No file changes provided.")

                # Run tests
                print("Running tests...")
                exit_code, output = self.executor.run_command(
                    task.test_command,
                    task_id=task.id,
                    timeout=self.config.background_task_timeout,
                    previous_timeout=self.executor.had_previous_timeout(task.id)
                )

                result_context = f"Task '{task.title}' " + ("passed" if exit_code == 0 else "failed")
                result_context += f"\nOutput:\n{output}"

                error_patterns = ['error', 'Error', 'ERROR', 'failed', 'Failed', 'FAILED', 'exception', 'Exception', 'EXCEPTION']
                has_error = any(pattern in output for pattern in error_patterns)

                if has_error and exit_code == 0:
                    print("Warning: Output contains error patterns despite exit code 0")

                if exit_code == 0 and not has_error:
                    print("Tests passed!")
                    self.task_manager.update_task_status(task.id, "completed")
                    self.retry_manager.reset_state(task.id)

                    # Commit with task checkpoint format
                    self._commit_task_changes(task, changed_files)
                    print("Changes committed.")
                    return True
                else:
                    print("Tests failed.")
                    error_msg = output[:500] if output else "Unknown error"
                    self.retry_manager.record_attempt(task.id, error_msg, False)

                    # Refine task list based on failure
                    self._refine_after_failure(task, coder_response, result_context, file_context, exit_code)

                    if attempt < max_retries - 1:
                        print("Retrying with refined approach...")
                        continue

                    # All in-run retries exhausted — record persistent error
                    print("All retries exhausted for this run.")
                    fatal = self.task_manager.record_task_error(task.id, error_msg)
                    if fatal:
                        raise FatalTaskError(task.id, task.failure_reason or error_msg)
                    return False

            except FatalTaskError:
                raise  # propagate upward to stop the run

            except Exception as e:
                print(f"An unexpected error occurred while processing task: {e}")
                error_msg = str(e)
                self.retry_manager.record_attempt(task.id, error_msg, False)

                if attempt < max_retries - 1:
                    print("Retrying after error...")
                    continue

                fatal = self.task_manager.record_task_error(task.id, error_msg)
                if fatal:
                    raise FatalTaskError(task.id, task.failure_reason or error_msg)
                return False

        return False

    def _commit_task_changes(self, task: SubTask, changed_files: List[str]):
        """
        Commit changes with task checkpoint format.

        Args:
            task: Completed task
            changed_files: List of changed file paths
        """
        commit_message = self.rollback_manager.create_task_commit(
            task_id=task.id,
            title=task.title,
            description=task.description,
            test_command=task.test_command,
            changed_files=changed_files
        )
        self.git_manager.commit(commit_message)

    def _breakdown_failed_task(self, task: SubTask, error: str):
        """
        Break down a failed task into smaller subtasks.

        Args:
            task: Failed task
            error: Error message
        """
        print(f"Breaking down failed task {task.id}...")
        self.task_manager.update_task_status(task.id, "failed")

        try:
            breakdown_context = f"""The following task failed after multiple retries:

Task ID: {task.id}
Title: {task.title}
Description: {task.description}
Test Command: {task.test_command}

Last Error: {error}

Please break this task down into 2-3 smaller, more manageable subtasks.
For each subtask, provide:
- id (use hierarchical format: {task.id}-1, {task.id}-2, etc.)
- title
- description
- test_command
- status: 'pending'

Return ONLY a JSON object with a 'tasks' array containing the new subtasks."""

            breakdown_response = self.coding_tool.query_json(
                breakdown_context,
                system_instruction="You are a task breakdown specialist. Return only valid JSON."
            )

            if "tasks" in breakdown_response:
                new_tasks = breakdown_response["tasks"]
                for new_task in new_tasks:
                    self.task_manager.add_task(SubTask(**new_task))
                print(f"Created {len(new_tasks)} subtasks from failed task.")
        except Exception as breakdown_error:
            print(f"Failed to break down task: {breakdown_error}")

    def _refine_after_failure(self, task: SubTask, coder_response: str, result_context: str,
                              file_context: str, exit_code: int):
        """
        Refine task list after a task failure.

        Args:
            task: Failed task
            coder_response: Last AI implementation attempt
            result_context: Test execution result
            file_context: Current codebase state
            exit_code: Exit code from test command
        """
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
            print(f"Task list updated. Total tasks: {len(self.task_manager.tasks)}")


def autonomous_coding(
    requirement: str,
    project_dir: str,
    recover: bool = False,
    max_tasks: Optional[int] = None,
    config_name: Optional[str] = None,
    tool: Optional[str] = None
):
    """
    Fully autonomous software development from requirement to completion.

    Args:
        requirement: High-level requirement description
        project_dir: Target project directory
        recover: Whether to skip planning and recover from crash
        max_tasks: Maximum number of tasks to execute
        config_name: Name of configuration to use (e.g., 'coding', 'harmonyos')
        tool: Coding tool to use ('opencode' or 'claude', default: 'opencode')
    """
    project_path = Path(project_dir).resolve()

    tool = (tool or "opencode").lower()
    if tool == "claude":
        coding_tool = ClaudeCodingTool()
        print("Using Claude as the coding tool.")
    else:
        coding_tool = OpenCodeCodingTool()

    # Load configuration
    config = None
    if config_name:
        from config_loader import load_config_by_name
        config = load_config_by_name(config_name)
        if config:
            print(f"Using configuration: {config_name}")
        else:
            print(f"Configuration '{config_name}' not found, using default")
            config = ConfigRegistry.get('coding')
    else:
        config = ConfigRegistry.get('coding')

    agent = AutonomousAgent(
        requirement=requirement,
        project_dir=project_path,
        coding_tool=coding_tool,
        config=config
    )

    if requirement and not recover:
        agent.plan()

    if max_tasks:
        agent.run(max_tasks=max_tasks, timeout=300)
    else:
        agent.run(timeout=300)
