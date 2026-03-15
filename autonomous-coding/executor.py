"""
Command Executor
================

Executes shell commands and captures output.
Supports both foreground and background execution.
"""

import subprocess
import time
from typing import Optional, Tuple

from background_manager import BackgroundManager


class Executor:
    """Executes shell commands in a project directory."""

    def __init__(self, project_dir: str, background_manager: Optional[BackgroundManager] = None):
        self.project_dir = project_dir
        self.background_manager = background_manager or BackgroundManager()
        self._timeout_history: dict = {}

    def run_command(
        self,
        command: str,
        task_id: Optional[str] = None,
        timeout: Optional[int] = None,
        previous_timeout: bool = False
    ) -> Tuple[int, str]:
        """
        Run command with smart timeout handling.

        Args:
            command: Shell command to execute
            task_id: Task identifier for background processes
            timeout: Timeout in seconds for foreground execution
            previous_timeout: If True, run as background process

        Returns:
            Tuple of (exit_code, output)
        """
        if previous_timeout and task_id:
            return self._run_background(command, task_id)
        else:
            return self._run_foreground(command, timeout)

    def _run_foreground(self, command: str, timeout: Optional[int] = None) -> Tuple[int, str]:
        """
        Run command in foreground with optional timeout.

        Args:
            command: Shell command to execute
            timeout: Optional timeout in seconds

        Returns:
            Tuple of (exit_code, output)
        """
        try:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=self.project_dir
            )

            output = ""
            start_time = time.time()

            while True:
                # Check timeout
                if timeout and (time.time() - start_time) > timeout:
                    process.terminate()
                    time.sleep(0.5)
                    if process.poll() is None:
                        process.kill()
                    return -1, f"Command timed out after {timeout} seconds"

                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    output += line

            return process.returncode, output
        except Exception as e:
            return 1, f"Error executing command: {e}"

    def _run_background(
        self,
        command: str,
        task_id: str,
        poll_interval: int = 30
    ) -> Tuple[int, str]:
        """
        Run command in background and poll for output.

        Args:
            command: Shell command to execute
            task_id: Task identifier
            poll_interval: Seconds between status checks

        Returns:
            Tuple of (exit_code, output)
        """
        self.background_manager.start_process(task_id, command, self.project_dir)

        while True:
            time.sleep(poll_interval)
            state = self.background_manager.check_process(task_id)

            if state is None:
                return 1, "Process state not found"

            if state.status == 'completed':
                output = self.background_manager.get_output(task_id)
                self.background_manager.cleanup(task_id)
                return 0, output

            elif state.status == 'failed':
                output = self.background_manager.get_output(task_id)
                self.background_manager.cleanup(task_id)
                return 1, output

            elif state.status == 'timeout':
                # Max lifetime exceeded (30 min)
                output = self.background_manager.get_output(task_id)
                self.background_manager.kill_process(task_id)
                self.background_manager.cleanup(task_id)
                return -1, f"Process timeout (exceeded {self.background_manager.MAX_LIFETIME_SECONDS}s)\n{output}"

            elif state.status == 'stuck':
                # No output for 3 minutes = stuck
                output = self.background_manager.get_output(task_id)
                self.background_manager.kill_process(task_id)
                self.background_manager.cleanup(task_id)
                return -1, f"Process stuck (no output for {self.background_manager.STUCK_THRESHOLD_SECONDS} seconds)\n{output}"

    def record_timeout(self, task_id: str, duration: int):
        """
        Record timeout duration for a task.

        Args:
            task_id: Task identifier
            duration: Timeout duration in seconds
        """
        if task_id not in self._timeout_history:
            self._timeout_history[task_id] = []
        self._timeout_history[task_id].append(duration)

    def had_previous_timeout(self, task_id: str) -> bool:
        """
        Check if task had a previous timeout.

        Args:
            task_id: Task identifier

        Returns:
            True if task had a previous timeout
        """
        return task_id in self._timeout_history and len(self._timeout_history[task_id]) > 0

    def cleanup(self):
        """Clean up all background processes."""
        self.background_manager.cleanup_all()
