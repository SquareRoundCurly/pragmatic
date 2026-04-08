"""Tests for the bash tool."""

import json

from pragmatic.tools.bash import BASH_TOOL, _bash_handler


def test_bash_tool_echo():
    result = json.loads(_bash_handler("echo hello"))
    assert result["stdout"] == "hello\n"
    assert result["stderr"] == ""
    assert result["exit_code"] == 0


def test_bash_tool_exit_code():
    result = json.loads(_bash_handler("exit 42"))
    assert result["exit_code"] == 42


def test_bash_tool_stderr():
    result = json.loads(_bash_handler("echo oops >&2"))
    assert result["stdout"] == ""
    assert result["stderr"] == "oops\n"
    assert result["exit_code"] == 0


def test_bash_tool_metadata():
    assert BASH_TOOL.name == "bash"
    schema = BASH_TOOL.to_openrouter()
    assert schema.function.name == "bash"
    assert "command" in schema.function.parameters["properties"]
