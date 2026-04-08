"""Tests for Agent deserialization (formerly AgentConfig)."""

import json
from unittest.mock import patch

import pytest

from pragmatic.agent import Agent, DEFAULT_MAX_ITERATIONS, DEFAULT_MODEL, DEFAULT_TOOLS


@patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key"})
class TestAgentConfig:
    def test_defaults(self):
        with patch("pragmatic.agent.OpenRouter"):
            agent = Agent()
        assert agent.model == DEFAULT_MODEL
        assert agent.max_iterations == DEFAULT_MAX_ITERATIONS
        assert "bash" in agent.tools

    def test_custom_values(self):
        with patch("pragmatic.agent.OpenRouter"):
            agent = Agent(model="anthropic/claude-3.5-sonnet", max_iterations=5, tools=["bash"])
        assert agent.model == "anthropic/claude-3.5-sonnet"
        assert agent.max_iterations == 5
        assert "bash" in agent.tools

    def test_from_file_full(self, tmp_path):
        path = tmp_path / "agent.json"
        path.write_text(json.dumps({
            "model": "google/gemini-2.0-flash-001",
            "max_iterations": 20,
            "tools": ["bash"],
        }))
        with patch("pragmatic.agent.OpenRouter"):
            agent = Agent.from_file(str(path))
        assert agent.model == "google/gemini-2.0-flash-001"
        assert agent.max_iterations == 20
        assert "bash" in agent.tools

    def test_from_file_partial(self, tmp_path):
        path = tmp_path / "agent.json"
        path.write_text(json.dumps({"model": "openai/gpt-4o"}))
        with patch("pragmatic.agent.OpenRouter"):
            agent = Agent.from_file(str(path))
        assert agent.model == "openai/gpt-4o"
        assert agent.max_iterations == DEFAULT_MAX_ITERATIONS

    def test_from_file_empty(self, tmp_path):
        path = tmp_path / "agent.json"
        path.write_text("{}")
        with patch("pragmatic.agent.OpenRouter"):
            agent = Agent.from_file(str(path))
        assert agent.model == DEFAULT_MODEL
        assert agent.max_iterations == DEFAULT_MAX_ITERATIONS

    def test_from_file_no_tools(self, tmp_path):
        path = tmp_path / "agent.json"
        path.write_text(json.dumps({"tools": []}))
        with patch("pragmatic.agent.OpenRouter"):
            agent = Agent.from_file(str(path))
        # Only finish tool should be present
        assert "finish" in agent.tools
        assert "bash" not in agent.tools

    def test_from_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            Agent.from_file("/nonexistent/agent.json")
