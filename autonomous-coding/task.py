"""
Task Data Model
================

SubTask data model representing a single task in the development workflow.
"""

from typing import Optional


class SubTask:
    """Represents a single subtask in the autonomous coding workflow."""
    
    def __init__(
        self,
        id: str,
        title: str,
        description: str,
        test_command: str,
        status: str = "pending",
        updated_time: Optional[str] = None
    ):
        self.id = id
        self.title = title
        self.description = description
        self.test_command = test_command
        self.status = status
        self.updated_time = updated_time
    
    def model_dump(self, mode: str = 'python', exclude_none: bool = False) -> dict:
        """
        Convert task to dictionary.
        
        Args:
            mode: Serialization mode (unused, kept for compatibility)
            exclude_none: Whether to exclude None values
            
        Returns:
            Dictionary representation of the task
        """
        result = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "test_command": self.test_command,
            "status": self.status
        }
        if not exclude_none or self.updated_time is not None:
            result["updated_time"] = self.updated_time
        return result
