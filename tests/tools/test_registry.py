"""Tests for tool registry and resolve_tools."""

import pytest

from pragmatic.tools import resolve_tools


def test_resolve_bash():
    tools = resolve_tools(["bash"])
    assert len(tools) == 1
    assert tools[0].name == "bash"


def test_resolve_empty():
    tools = resolve_tools([])
    assert tools == []


def test_resolve_unknown():
    with pytest.raises(ValueError, match="Unknown tool"):
        resolve_tools(["nonexistent"])
