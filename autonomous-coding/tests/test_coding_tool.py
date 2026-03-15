"""Unit tests for CodingTool implementations."""

import json
import os
import sys
from unittest.mock import patch, MagicMock
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from coding_tool import OpenCodeCodingTool, ClaudeCodingTool


def _make_completed_process(stdout="output", returncode=0):
    mock = MagicMock()
    mock.returncode = returncode
    mock.stdout = stdout
    mock.stderr = ""
    return mock


class TestOpenCodeCodingTool:
    def test_query_returns_stdout(self):
        tool = OpenCodeCodingTool()
        with patch("subprocess.run", return_value=_make_completed_process("hello")) as mock_run:
            result = tool.query("do something")
            assert result == "hello"
            mock_run.assert_called_once()

    def test_query_prepends_system_instruction(self):
        tool = OpenCodeCodingTool()
        with patch("subprocess.run", return_value=_make_completed_process("ok")) as mock_run:
            tool.query("task prompt", system_instruction="be helpful")
            call_input = mock_run.call_args.kwargs["input"]
            assert "be helpful" in call_input
            assert "task prompt" in call_input

    def test_query_raises_on_nonzero_exit(self):
        tool = OpenCodeCodingTool()
        with patch("subprocess.run", return_value=_make_completed_process("fail", returncode=1)):
            try:
                tool.query("prompt")
                assert False, "Expected exception"
            except Exception as e:
                assert "OpenCode failed" in str(e)

    def test_query_json_parses_json(self):
        tool = OpenCodeCodingTool()
        payload = json.dumps({"tasks": [{"id": "1"}]})
        with patch("subprocess.run", return_value=_make_completed_process(payload)):
            result = tool.query_json("give me json")
            assert result == {"tasks": [{"id": "1"}]}

    def test_query_json_extracts_json_from_prose(self):
        tool = OpenCodeCodingTool()
        payload = 'Here is the result: {"tasks": []} and that is it.'
        with patch("subprocess.run", return_value=_make_completed_process(payload)):
            result = tool.query_json("give me json")
            assert result == {"tasks": []}

    def test_query_timeout_raises_timeout_error(self):
        from concurrent.futures import TimeoutError as FuturesTimeout
        tool = OpenCodeCodingTool()
        with patch("subprocess.run", side_effect=lambda *a, **kw: __import__("time").sleep(10)):
            try:
                tool.query("prompt", timeout=1)
                assert False, "Expected TimeoutError"
            except TimeoutError as e:
                assert "timed out" in str(e)


class TestClaudeCodingTool:
    def test_query_calls_claude_cli(self):
        tool = ClaudeCodingTool()
        with patch("subprocess.run", return_value=_make_completed_process("claude output")) as mock_run:
            result = tool.query("write a function")
            assert result == "claude output"
            cmd = mock_run.call_args.args[0]
            assert "claude" in cmd
            assert "--dangerously-skip-permissions" in cmd
            assert "-p" in cmd

    def test_query_includes_prompt_as_p_argument(self):
        tool = ClaudeCodingTool()
        with patch("subprocess.run", return_value=_make_completed_process("ok")) as mock_run:
            tool.query("my specific prompt")
            cmd = mock_run.call_args.args[0]
            idx = cmd.index("-p")
            assert cmd[idx + 1] == "my specific prompt"

    def test_query_appends_system_prompt(self):
        tool = ClaudeCodingTool()
        with patch("subprocess.run", return_value=_make_completed_process("ok")) as mock_run:
            tool.query("task", system_instruction="be careful")
            cmd = mock_run.call_args.args[0]
            assert "--append-system-prompt" in cmd
            idx = cmd.index("--append-system-prompt")
            assert cmd[idx + 1] == "be careful"

    def test_query_includes_model_flag(self):
        tool = ClaudeCodingTool(model="claude-opus-4-6")
        with patch("subprocess.run", return_value=_make_completed_process("ok")) as mock_run:
            tool.query("prompt")
            cmd = mock_run.call_args.args[0]
            assert "--model" in cmd
            idx = cmd.index("--model")
            assert cmd[idx + 1] == "claude-opus-4-6"

    def test_query_raises_on_cli_failure(self):
        tool = ClaudeCodingTool()
        with patch("subprocess.run", return_value=_make_completed_process("error msg", returncode=1)):
            try:
                tool.query("prompt")
                assert False, "Expected exception"
            except Exception as e:
                assert "Claude CLI failed" in str(e)

    def test_query_json_parses_json(self):
        tool = ClaudeCodingTool()
        payload = '{"tasks": [{"id": "1", "title": "T"}]}'
        with patch("subprocess.run", return_value=_make_completed_process(payload)):
            result = tool.query_json("plan this")
            assert "tasks" in result

    def test_query_json_appends_json_instruction(self):
        tool = ClaudeCodingTool()
        with patch("subprocess.run", return_value=_make_completed_process("{}")) as mock_run:
            tool.query_json("plan this")
            cmd = mock_run.call_args.args[0]
            prompt_idx = cmd.index("-p")
            prompt_text = cmd[prompt_idx + 1]
            assert "JSON" in prompt_text

    def test_default_model_is_sonnet(self):
        tool = ClaudeCodingTool()
        assert tool.model == ClaudeCodingTool.DEFAULT_MODEL

    def test_query_timeout_raises_timeout_error(self):
        tool = ClaudeCodingTool()
        with patch("subprocess.run", side_effect=lambda *a, **kw: __import__("time").sleep(10)):
            try:
                tool.query("prompt", timeout=1)
                assert False, "Expected TimeoutError"
            except TimeoutError as e:
                assert "timed out" in str(e)
