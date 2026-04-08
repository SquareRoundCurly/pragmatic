"""Integration tests for sandboxed bash with permissions.

These tests invoke the sandboxed bash handler directly (no LLM needed)
to verify that bwrap enforces read/write permissions correctly.

Each test sets up a temp directory with fixture files, builds an Agent
from an agent.json, and calls the sandboxed bash tool handler.
"""

import json
import os

from tests.integration.conftest import requires_bwrap

from pragmatic.sandbox.spec import SandboxSpec
from pragmatic.tools.bash import sandboxed_bash_tool


@requires_bwrap
class TestSandboxWriteAllowed:
    """Agent has write permission to a directory and can write files there."""

    def test_write_succeeds(self, tmp_path):
        # Set up: writable workspace
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        # agent.json equivalent permissions
        spec = SandboxSpec(
            command=[],
            workdir=str(workspace),
            rw_binds=[(str(workspace), str(workspace))],
        )
        tool = sandboxed_bash_tool(spec)

        # Agent writes result.txt
        result = json.loads(tool.handler("echo 42 > result.txt"))
        assert result["exit_code"] == 0, f"Write failed: {result['stderr']}"

        # Verify the file was actually written
        result_file = workspace / "result.txt"
        assert result_file.exists()
        assert result_file.read_text().strip() == "42"

    def test_read_own_output(self, tmp_path):
        # Set up: writable workspace with a seed file
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        (workspace / "input.txt").write_text("hello")

        spec = SandboxSpec(
            command=[],
            workdir=str(workspace),
            rw_binds=[(str(workspace), str(workspace))],
        )
        tool = sandboxed_bash_tool(spec)

        # Read from rw-bound path
        result = json.loads(tool.handler("cat input.txt"))
        assert result["exit_code"] == 0
        assert result["stdout"].strip() == "hello"


@requires_bwrap
class TestSandboxWriteDenied:
    """Agent lacks write permission and fails when trying to write."""

    def test_write_to_readonly_fails(self, tmp_path):
        # Set up: workspace is read-only
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        spec = SandboxSpec(
            command=[],
            workdir=str(workspace),
            ro_binds=[(str(workspace), str(workspace))],
        )
        tool = sandboxed_bash_tool(spec)

        # Attempt to write — should fail
        result = json.loads(tool.handler("echo 42 > result.txt"))
        assert result["exit_code"] != 0

        # File must not exist on host
        assert not (workspace / "result.txt").exists()

    def test_read_from_readonly_succeeds(self, tmp_path):
        # Set up: workspace is read-only with a file in it
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        (workspace / "data.txt").write_text("secret")

        spec = SandboxSpec(
            command=[],
            workdir=str(workspace),
            ro_binds=[(str(workspace), str(workspace))],
        )
        tool = sandboxed_bash_tool(spec)

        # Read should still work
        result = json.loads(tool.handler("cat data.txt"))
        assert result["exit_code"] == 0
        assert result["stdout"].strip() == "secret"

    def test_write_to_unbound_path_fails(self, tmp_path):
        # Set up: writable workspace, but agent tries to escape
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        outside = tmp_path / "outside"
        outside.mkdir()

        spec = SandboxSpec(
            command=[],
            workdir=str(workspace),
            rw_binds=[(str(workspace), str(workspace))],
        )
        tool = sandboxed_bash_tool(spec)

        # Try to write outside the permitted path
        result = json.loads(tool.handler(f"echo pwned > {outside}/hack.txt"))
        assert result["exit_code"] != 0
        assert not (outside / "hack.txt").exists()


@requires_bwrap
class TestSandboxFromAgentJson:
    """End-to-end: load agent.json with permissions, verify sandbox behavior."""

    def test_full_flow_write_allowed(self, tmp_path):
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        agent_json = tmp_path / "agent.json"
        agent_json.write_text(json.dumps({
            "model": "openai/gpt-4.1-nano",
            "tools": ["bash"],
            "permissions": [
                {"write": str(workspace)},
            ],
        }))

        # Load agent and grab the sandboxed bash handler
        from unittest.mock import patch
        with patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key"}), \
             patch("pragmatic.agent.OpenRouter"):
            from pragmatic.agent import Agent
            agent = Agent.from_file(str(agent_json))

        bash = agent.tools["bash"]
        result = json.loads(bash.handler("echo success > out.txt"))
        assert result["exit_code"] == 0
        assert (workspace / "out.txt").read_text().strip() == "success"

    def test_full_flow_write_denied(self, tmp_path):
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        agent_json = tmp_path / "agent.json"
        agent_json.write_text(json.dumps({
            "model": "openai/gpt-4.1-nano",
            "tools": ["bash"],
            "permissions": [
                {"read": str(workspace)},
            ],
        }))

        from unittest.mock import patch
        with patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key"}), \
             patch("pragmatic.agent.OpenRouter"):
            from pragmatic.agent import Agent
            agent = Agent.from_file(str(agent_json))

        bash = agent.tools["bash"]
        result = json.loads(bash.handler("echo fail > out.txt"))
        assert result["exit_code"] != 0
        assert not (workspace / "out.txt").exists()
