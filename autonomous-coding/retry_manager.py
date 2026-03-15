"""
Retry Manager
=============

Manages retry logic for failed tasks.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class RetryState:
    """Tracks retry state for a task."""
    task_id: str
    attempt_count: int = 0
    last_error: str = ""
    last_attempt_time: Optional[datetime] = None
    retry_history: List[Dict] = field(default_factory=list)


class RetryManager:
    """Manages retry logic for failed tasks."""

    MAX_RETRIES = 5

    def __init__(self):
        self._retry_states: Dict[str, RetryState] = {}

    def should_retry(self, task_id: str, error: str) -> bool:
        """
        Determine if task should be retried.

        Args:
            task_id: Task identifier
            error: Error message from last attempt

        Returns:
            True if task should be retried, False otherwise
        """
        state = self._get_or_create_state(task_id)
        return state.attempt_count < self.MAX_RETRIES

    def record_attempt(self, task_id: str, error: str, success: bool):
        """
        Record an attempt for tracking.

        Args:
            task_id: Task identifier
            error: Error message (empty if success)
            success: Whether the attempt succeeded
        """
        state = self._get_or_create_state(task_id)

        if not success:
            state.attempt_count += 1
            state.last_error = error

        state.last_attempt_time = datetime.utcnow()
        state.retry_history.append({
            "attempt": state.attempt_count,
            "error": error,
            "success": success,
            "timestamp": state.last_attempt_time.isoformat()
        })

    def get_retry_prompt_modifier(self, task_id: str) -> str:
        """
        Generate prompt modifier based on retry history.

        Args:
            task_id: Task identifier

        Returns:
            Prompt modifier string to help guide the next attempt
        """
        state = self._retry_states.get(task_id)
        if not state or state.attempt_count == 0:
            return ""

        modifier_parts = [f"\n\n[RETRY CONTEXT - Attempt {state.attempt_count + 1} of {self.MAX_RETRIES}]"]

        if state.attempt_count <= 3:
            # Early retries: provide error context
            modifier_parts.append(f"Previous attempt failed with error:\n{state.last_error}")
            modifier_parts.append("\nPlease analyze the error and try a different approach.")
        else:
            # Later retries: suggest simplification
            modifier_parts.append(f"Multiple attempts have failed. Last error:\n{state.last_error}")
            modifier_parts.append("\nPlease consider:")
            modifier_parts.append("1. Breaking down the task into simpler steps")
            modifier_parts.append("2. Using a completely different approach")
            modifier_parts.append("3. Checking for environmental issues (missing dependencies, permissions)")

        # Add history summary for later attempts
        if state.attempt_count >= 2 and len(state.retry_history) > 1:
            modifier_parts.append("\n\nSummary of previous attempts:")
            for i, hist in enumerate(state.retry_history[-3:], 1):  # Last 3 attempts
                modifier_parts.append(f"\nAttempt {hist['attempt']}: {'Success' if hist['success'] else 'Failed'}")
                if not hist['success'] and hist['error']:
                    modifier_parts.append(f"  Error: {hist['error'][:200]}...")

        return "\n".join(modifier_parts)

    def get_state(self, task_id: str) -> Optional[RetryState]:
        """
        Get retry state for a task.

        Args:
            task_id: Task identifier

        Returns:
            RetryState or None if not found
        """
        return self._retry_states.get(task_id)

    def reset_state(self, task_id: str):
        """
        Reset retry state for a task.

        Args:
            task_id: Task identifier
        """
        if task_id in self._retry_states:
            del self._retry_states[task_id]

    def clear_all(self):
        """Clear all retry states."""
        self._retry_states.clear()

    def _get_or_create_state(self, task_id: str) -> RetryState:
        """Get or create retry state for a task."""
        if task_id not in self._retry_states:
            self._retry_states[task_id] = RetryState(task_id=task_id)
        return self._retry_states[task_id]
