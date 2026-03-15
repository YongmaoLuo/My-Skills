"""
Autonomous Coding Skill
=====================

Fully autonomous software development from requirement to completion.
"""

from agent import AutonomousAgent, autonomous_coding
from config import AgentConfig
from config_registry import ConfigRegistry
from config_loader import load_config, load_config_by_name
from retry_manager import RetryManager, RetryState
from background_manager import BackgroundManager, ProcessState
from rollback_manager import RollbackManager, TaskCheckpoint
from executor import Executor
from task import SubTask
from task_manager import TaskManager

__version__ = "4.0.0"
__all__ = [
    # Main interface
    "AutonomousAgent",
    "autonomous_coding",

    # Configuration
    "AgentConfig",
    "ConfigRegistry",
    "load_config",
    "load_config_by_name",

    # Retry mechanism
    "RetryManager",
    "RetryState",

    # Background process management
    "BackgroundManager",
    "ProcessState",

    # Rollback mechanism
    "RollbackManager",
    "TaskCheckpoint",

    # Core components
    "Executor",
    "SubTask",
    "TaskManager",
]
