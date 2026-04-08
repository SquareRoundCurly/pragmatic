"""Tool definitions for the agent."""

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
