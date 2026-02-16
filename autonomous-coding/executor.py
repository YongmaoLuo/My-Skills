"""
Command Executor
===============

Executes shell commands and captures output.
"""

import subprocess


class Executor:
    """Executes shell commands in a project directory."""
    
    def __init__(self, project_dir: str):
        self.project_dir = project_dir
    
    def run_command(self, command: str) -> tuple[int, str]:
        """
        Run a shell command and capture output.
        
        Args:
            command: Shell command to execute
            
        Returns:
            Tuple of (exit_code, output)
        """
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=self.project_dir
        )
        
        output = ""
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                output += line
        
        return process.returncode, output
