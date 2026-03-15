"""
Coding Tool Interface
==================

Abstract base class for AI coding tools and implementations.
"""

from abc import ABC, abstractmethod
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError


class CodingTool(ABC):
    """Abstract base class for AI coding tools."""
    
    @abstractmethod
    def query(self, prompt: str, system_instruction: Optional[str] = None, 
              retries: int = 3, timeout: Optional[int] = None) -> str:
        """
        Query the AI coding tool.
        
        Args:
            prompt: The prompt to send to the AI
            system_instruction: Optional system instruction
            retries: Number of retry attempts
            timeout: Optional timeout in seconds
            
        Returns:
            AI response as string
        """
        pass

    @abstractmethod
    def query_json(self, prompt: str, system_instruction: Optional[str] = None,
                 retries: int = 3, timeout: Optional[int] = None) -> dict:
        """
        Query the AI coding tool and expect JSON response.
        
        Args:
            prompt: The prompt to send to the AI
            system_instruction: Optional system instruction
            retries: Number of retry attempts
            timeout: Optional timeout in seconds
            
        Returns:
            AI response as dict
        """
        pass


class ClaudeCodingTool(CodingTool):
    """Claude Code CLI tool — runs `claude --dangerously-skip-permissions -p <prompt>`."""

    DEFAULT_MODEL = "claude-sonnet-4-6"

    def __init__(self, model: Optional[str] = None):
        self.model = model or self.DEFAULT_MODEL

    def _run_claude(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        """Run Claude Code CLI in non-interactive print mode."""
        import subprocess
        cmd = [
            "claude",
            "--dangerously-skip-permissions",
            "-p", prompt,
        ]
        if system_instruction:
            cmd += ["--append-system-prompt", system_instruction]
        if self.model:
            cmd += ["--model", self.model]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Claude CLI failed: {result.stderr or result.stdout}")
        return result.stdout

    def query(self, prompt: str, system_instruction: Optional[str] = None,
              retries: int = 3, timeout: Optional[int] = None) -> str:
        """Run a subtask through Claude Code CLI."""
        def _query_internal():
            return self._run_claude(prompt, system_instruction)

        if timeout is None:
            return _query_internal()

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_query_internal)
            try:
                return future.result(timeout=timeout)
            except FuturesTimeoutError:
                future.cancel()
                raise TimeoutError(f"Query timed out after {timeout} seconds")

    def query_json(self, prompt: str, system_instruction: Optional[str] = None,
                   retries: int = 3, timeout: Optional[int] = None) -> dict:
        """Run a subtask through Claude Code CLI and parse the JSON response."""
        import json

        json_prompt = prompt + "\n\nIMPORTANT: Return ONLY the JSON object requested, no markdown fencing."

        def _query_json_internal():
            response_text = self._run_claude(json_prompt, system_instruction)
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start != -1 and end > start:
                return json.loads(response_text[start:end])
            return json.loads(response_text)

        if timeout is None:
            return _query_json_internal()

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_query_json_internal)
            try:
                return future.result(timeout=timeout)
            except FuturesTimeoutError:
                future.cancel()
                raise TimeoutError(f"Query timed out after {timeout} seconds")


class OpenCodeCodingTool(CodingTool):
    """OpenCode AI coding tool using opencode CLI."""
    
    def __init__(self):
        pass
    
    def _run_opencode(self, prompt: str) -> str:
        """Run opencode CLI."""
        import subprocess
        result = subprocess.run(
            ["opencode", "run"],
            input=prompt,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            raise Exception(f"OpenCode failed: {result.stderr or result.stdout}")
        return result.stdout
    
    def query(self, prompt: str, system_instruction: Optional[str] = None,
              retries: int = 3, timeout: Optional[int] = None) -> str:
        """Query OpenCode AI."""
        def _query_internal():
            full_prompt = prompt
            if system_instruction:
                full_prompt = f"{system_instruction}\n\nTask:\n{prompt}"
            
            return self._run_opencode(full_prompt)
        
        if timeout is None:
            return _query_internal()
        
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_query_internal)
            try:
                return future.result(timeout=timeout)
            except FuturesTimeoutError:
                future.cancel()
                raise TimeoutError(f"Query timed out after {timeout} seconds")
    
    def query_json(self, prompt: str, system_instruction: Optional[str] = None,
                 retries: int = 3, timeout: Optional[int] = None) -> dict:
        """Query OpenCode AI and expect JSON response."""
        import json
        
        def _query_json_internal():
            full_prompt = prompt
            if system_instruction:
                full_prompt = f"{system_instruction}\n\nTask:\n{prompt}"
            
            full_prompt += "\n\nIMPORTANT: Return ONLY the JSON object requested."
            
            response_text = self._run_opencode(full_prompt)
            
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start != -1 and end != 0:
                return json.loads(response_text[start:end])
            return json.loads(response_text)
        
        if timeout is None:
            return _query_json_internal()
        
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_query_json_internal)
            try:
                return future.result(timeout=timeout)
            except FuturesTimeoutError:
                future.cancel()
                raise TimeoutError(f"Query timed out after {timeout} seconds")
