"""Simple agentic loop with tool support."""

import json
import os
import sys

from dotenv import load_dotenv
from openrouter import OpenRouter
from openrouter.components import (
    ChatToolMessage,
    ChatUserMessage,
)

from pragmatic.tools import Tool
from pragmatic.tools.finish import FINISH_TOOL


class Agent:
    """A simple agentic loop that sends a prompt to an LLM and processes tool calls."""

    def __init__(self, model: str = "openai/gpt-4.1-nano", tools: list[Tool] | None = None, max_iterations: int = 10):
        load_dotenv()
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise RuntimeError("OPENROUTER_API_KEY environment variable not set")

        self.client = OpenRouter(api_key=api_key)
        self.model = model
        self.max_iterations = max_iterations

        self.tools: dict[str, Tool] = {FINISH_TOOL.name: FINISH_TOOL}
        for tool in tools or []:
            self.tools[tool.name] = tool

    def _log(self, role: str, content: str) -> None:
        print(f"[{role}] {content}", file=sys.stderr)

    def run(self, prompt: str) -> dict:
        """Run the agent loop. Returns the finish result or a timeout dict."""
        turns: list = [ChatUserMessage(role="user", content=prompt)]
        openrouter_tools = [t.to_openrouter() for t in self.tools.values()]

        self._log("user", prompt)

        for i in range(self.max_iterations):
            self._log("system", f"--- iteration {i + 1}/{self.max_iterations} ---")

            response = self.client.chat.send(
                model=self.model,
                messages=turns,
                tools=openrouter_tools,
            )

            choice = response.choices[0]
            message = choice.message

            # Append the raw response message as the assistant turn
            turns.append({"role": "assistant", "content": message.content or "", "tool_calls": [
                {"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                for tc in (message.tool_calls or [])
            ] or None})

            # No tool calls — model just responded with text
            if not message.tool_calls:
                self._log("assistant", message.content or "")
                if choice.finish_reason == "stop":
                    return {"success": True, "reason": message.content or ""}
                continue

            if message.content:
                self._log("assistant", message.content)

            # Process each tool call
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)

                self._log("tool_call", f"{tool_name}({json.dumps(args)})")

                if tool_name == "finish":
                    self._log("system", f"finished: success={args.get('success')} reason={args.get('reason')}")
                    return args

                tool = self.tools.get(tool_name)
                if tool:
                    result = tool.handler(**args)
                else:
                    result = json.dumps({"error": f"Unknown tool: {tool_name}"})

                self._log("tool_result", result)

                turns.append(
                    ChatToolMessage(
                        role="tool",
                        tool_call_id=tool_call.id,
                        content=result,
                    )
                )

        self._log("system", f"max iterations ({self.max_iterations}) reached")
        return {"success": False, "reason": f"Max iterations ({self.max_iterations}) reached"}
