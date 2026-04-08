"""Tests for agent permissions and sandboxing."""

import json
import os
from unittest.mock import patch

from pragmatic.agent import Agent, _permissions_to_sandbox


def test_permissions_to_sandbox_read():
    perms = [{"read": "/data"}]
    spec = _permissions_to_sandbox(perms)
    assert ("/data", "/data") in spec.ro_binds
    assert spec.rw_binds == []


def test_permissions_to_sandbox_write():
    perms = [{"write": "/output"}]
    spec = _permissions_to_sandbox(perms)
    assert ("/output", "/output") in spec.rw_binds
    assert spec.ro_binds == []
    assert spec.workdir == "/output"


def test_permissions_to_sandbox_mixed():
    perms = [
        {"read": "/src"},
        {"read": "/lib"},
        {"write": "/out"},
    ]
    spec = _permissions_to_sandbox(perms)
    assert ("/src", "/src") in spec.ro_binds
    assert ("/lib", "/lib") in spec.ro_binds
    assert ("/out", "/out") in spec.rw_binds
    assert spec.workdir == "/src"


def test_permissions_to_sandbox_relative_paths():
    perms = [{"read": "relative/path"}]
    spec = _permissions_to_sandbox(perms)
    expected = os.path.abspath("relative/path")
    assert (expected, expected) in spec.ro_binds


@patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key"})
class TestAgentPermissions:
    def test_no_permissions_uses_regular_bash(self):
        with patch("pragmatic.agent.OpenRouter"):
            agent = Agent()
        # handler should be the plain _bash_handler
        from pragmatic.tools.bash import _bash_handler
        assert agent.tools["bash"].handler is _bash_handler

    def test_permissions_swaps_to_sandboxed_bash(self):
        perms = [{"read": "/data"}, {"write": "/out"}]
        with patch("pragmatic.agent.OpenRouter"):
            agent = Agent(permissions=perms)
        # handler should NOT be the plain _bash_handler
        from pragmatic.tools.bash import _bash_handler
        assert agent.tools["bash"].handler is not _bash_handler

    def test_from_file_with_permissions(self, tmp_path):
        path = tmp_path / "agent.json"
        path.write_text(json.dumps({
            "permissions": [
                {"read": "/src"},
                {"write": "/out"},
            ],
        }))
        with patch("pragmatic.agent.OpenRouter"):
            agent = Agent.from_file(str(path))
        assert agent.permissions == [{"read": "/src"}, {"write": "/out"}]
        from pragmatic.tools.bash import _bash_handler
        assert agent.tools["bash"].handler is not _bash_handler

    def test_from_file_without_permissions(self, tmp_path):
        path = tmp_path / "agent.json"
        path.write_text("{}")
        with patch("pragmatic.agent.OpenRouter"):
            agent = Agent.from_file(str(path))
        assert agent.permissions is None
        from pragmatic.tools.bash import _bash_handler
        assert agent.tools["bash"].handler is _bash_handler

    def test_empty_permissions_no_sandbox(self):
        with patch("pragmatic.agent.OpenRouter"):
            agent = Agent(permissions=[])
        from pragmatic.tools.bash import _bash_handler
        # Empty list is falsy, so no sandbox
        assert agent.tools["bash"].handler is _bash_handler
