"""Tool definitions for the agent."""

from __future__ import annotations

from openrouter.components import (
    ChatFunctionToolFunction,
    ChatFunctionToolFunctionFunction,
)


class Tool:
    """A tool that the agent can call."""

    def __init__(self, name: str, description: str, parameters: dict, handler):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.handler = handler

    def to_openrouter(self) -> ChatFunctionToolFunction:
        return ChatFunctionToolFunction(
            type="function",
            function=ChatFunctionToolFunctionFunction(
                name=self.name,
                description=self.description,
                parameters=self.parameters,
            ),
        )


TOOL_REGISTRY: dict[str, Tool] = {}


def _register_builtin_tools() -> None:
    from pragmatic.tools.bash import BASH_TOOL
    TOOL_REGISTRY[BASH_TOOL.name] = BASH_TOOL


def resolve_tools(names: list[str]) -> list[Tool]:
    """Resolve a list of tool names to Tool instances."""
    if not TOOL_REGISTRY:
        _register_builtin_tools()
    tools = []
    for name in names:
        if name not in TOOL_REGISTRY:
            raise ValueError(f"Unknown tool: {name!r}")
        tools.append(TOOL_REGISTRY[name])
    return tools
