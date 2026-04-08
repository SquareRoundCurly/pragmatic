"""Tests for the agent module."""

import json
from unittest.mock import MagicMock, patch

import pytest

from pragmatic.agent import Agent
from pragmatic.tools import Tool
from pragmatic.tools.finish import FINISH_TOOL


def _make_response(content=None, tool_calls=None, finish_reason="stop"):
    """Build a mock OpenRouter response."""
    message = MagicMock()
    message.content = content
    message.tool_calls = tool_calls

    choice = MagicMock()
    choice.message = message
    choice.finish_reason = finish_reason

    response = MagicMock()
    response.choices = [choice]
    return response


def _make_tool_call(call_id, name, arguments):
    tc = MagicMock()
    tc.id = call_id
    tc.function.name = name
    tc.function.arguments = json.dumps(arguments)
    return tc


@patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key"})
class TestAgent:
    def test_finish_on_first_call(self):
        """Model immediately calls finish."""
        finish_call = _make_tool_call("call_1", "finish", {"success": True, "reason": "Done"})
        response = _make_response(tool_calls=[finish_call], finish_reason="tool_calls")

        with patch("pragmatic.agent.OpenRouter") as mock_or:
            mock_or.return_value.chat.send.return_value = response
            agent = Agent()
            result = agent.run("Do something")

        assert result == {"success": True, "reason": "Done"}

    def test_text_response_returns(self):
        """Model responds with text (no tool calls) and stops."""
        response = _make_response(content="Here is the answer", finish_reason="stop")

        with patch("pragmatic.agent.OpenRouter") as mock_or:
            mock_or.return_value.chat.send.return_value = response
            agent = Agent()
            result = agent.run("What is 2+2?")

        assert result == {"success": True, "reason": "Here is the answer"}

    def test_custom_tool_then_finish(self):
        """Model calls a custom tool, gets result, then finishes."""
        add_tool = Tool(
            name="add",
            description="Add two numbers",
            parameters={
                "type": "object",
                "properties": {
                    "a": {"type": "number"},
                    "b": {"type": "number"},
                },
                "required": ["a", "b"],
            },
            handler=lambda a, b: json.dumps({"result": a + b}),
        )

        tool_call = _make_tool_call("call_1", "add", {"a": 2, "b": 3})
        response1 = _make_response(tool_calls=[tool_call], finish_reason="tool_calls")

        finish_call = _make_tool_call("call_2", "finish", {"success": True, "reason": "2+3=5"})
        response2 = _make_response(tool_calls=[finish_call], finish_reason="tool_calls")

        with patch("pragmatic.agent.OpenRouter") as mock_or:
            mock_or.return_value.chat.send.side_effect = [response1, response2]
            agent = Agent(tools=[add_tool])
            result = agent.run("Add 2 and 3")

        assert result == {"success": True, "reason": "2+3=5"}
        assert mock_or.return_value.chat.send.call_count == 2

    def test_max_iterations(self):
        """Agent stops after max iterations."""
        response = _make_response(content="thinking...", finish_reason="length")

        with patch("pragmatic.agent.OpenRouter") as mock_or:
            mock_or.return_value.chat.send.return_value = response
            agent = Agent(max_iterations=3)
            result = agent.run("Loop forever")

        assert result["success"] is False
        assert "3" in result["reason"]
        assert mock_or.return_value.chat.send.call_count == 3

    def test_unknown_tool_returns_error(self):
        """Unknown tool call gets error result, then model finishes."""
        bad_call = _make_tool_call("call_1", "nonexistent", {})
        response1 = _make_response(tool_calls=[bad_call], finish_reason="tool_calls")

        finish_call = _make_tool_call("call_2", "finish", {"success": False, "reason": "tool not found"})
        response2 = _make_response(tool_calls=[finish_call], finish_reason="tool_calls")

        with patch("pragmatic.agent.OpenRouter") as mock_or:
            mock_or.return_value.chat.send.side_effect = [response1, response2]
            agent = Agent()
            result = agent.run("Use nonexistent tool")

        assert result == {"success": False, "reason": "tool not found"}

    def test_finish_tool_definition(self):
        """FINISH_TOOL has correct structure."""
        openrouter_def = FINISH_TOOL.to_openrouter()
        assert openrouter_def.function.name == "finish"
        assert "success" in openrouter_def.function.parameters["properties"]
        assert "reason" in openrouter_def.function.parameters["properties"]


def test_missing_api_key():
    with patch("pragmatic.agent.load_dotenv"), patch.dict("os.environ", {}, clear=True):
        with pytest.raises(RuntimeError, match="OPENROUTER_API_KEY"):
            Agent()
