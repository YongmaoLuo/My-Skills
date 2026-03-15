"""
Agent Configuration
===================

Configuration for domain-specific agent behavior.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class AgentConfig:
    """Configuration for domain-specific agent behavior."""

    # Planner prompts
    planner_system_prompt: str  # System prompt for planning
    planner_task_template: Optional[str] = None  # Template for task generation (optional)

    # Executor prompts
    executor_system_prompt: str = ""  # System prompt for execution
    executor_task_template: Optional[str] = None  # Template for task execution (optional)

    # Refiner prompts
    refiner_system_prompt: str = ""  # System prompt for refinement

    # Domain context
    domain_knowledge: str = ""  # Background knowledge for the domain
    file_patterns: List[str] = field(default_factory=lambda: ["*"])  # Relevant file patterns

    # Behavior settings
    max_retries: int = 5
    background_task_timeout: int = 180  # 3 minutes of no output = stuck
