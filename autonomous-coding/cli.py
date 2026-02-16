"""
Command Line Interface
====================

CLI for autonomous coding skill.
"""

import argparse
from pathlib import Path
from typing import Optional

from agent import autonomous_coding


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(description="Autonomous Coding CLI")
    parser.add_argument("requirement", nargs="?", help="The high-level requirement")
    parser.add_argument("--workspace", "-w", default=".", help="Project directory (default: current directory)")
    parser.add_argument("--dir", help="Project directory (deprecated, use --workspace)")
    parser.add_argument("--recover", action="store_true", help="Recover from previous crash (skip planning)")
    parser.add_argument("--max-tasks", type=int, default=None, help="Maximum tasks to execute")
    args = parser.parse_args()
    
    workspace_dir = args.workspace
    if args.dir:
        workspace_dir = args.dir
    
    autonomous_coding(
        requirement=args.requirement,
        project_dir=workspace_dir,
        recover=args.recover,
        max_tasks=args.max_tasks
    )


if __name__ == "__main__":
    main()
