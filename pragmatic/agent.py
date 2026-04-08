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

from pragmatic.sandbox.spec import SandboxSpec
from pragmatic.tools import Tool, resolve_tools
from pragmatic.tools.bash import sandboxed_bash_tool
from pragmatic.tools.finish import FINISH_TOOL

DEFAULT_MODEL = "openai/gpt-4.1-nano"
DEFAULT_MAX_ITERATIONS = 10
DEFAULT_TOOLS = ["bash"]


def _permissions_to_sandbox(permissions: list[dict[str, str]]) -> SandboxSpec:
    """Convert a permissions list to a SandboxSpec."""
    ro_binds = []
    rw_binds = []
    workdir = None
    for entry in permissions:
        path = os.path.abspath(entry.get("read") or entry.get("write", ""))
        if "read" in entry:
            ro_binds.append((path, path))
        elif "write" in entry:
            rw_binds.append((path, path))
        if workdir is None:
            workdir = path
    return SandboxSpec(
        command=[],  # filled per invocation
        workdir=workdir,
        ro_binds=ro_binds,
        rw_binds=rw_binds,
    )


class Agent:
    """A simple agentic loop that sends a prompt to an LLM and processes tool calls."""

    def __init__(self, model: str = DEFAULT_MODEL, max_iterations: int = DEFAULT_MAX_ITERATIONS,
                 tools: list[str] | None = None, permissions: list[dict[str, str]] | None = None):
        load_dotenv()
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise RuntimeError("OPENROUTER_API_KEY environment variable not set")

        self.model = model
        self.max_iterations = max_iterations
        self.permissions = permissions
        self.client = OpenRouter(api_key=api_key)

        self.tools: dict[str, Tool] = {FINISH_TOOL.name: FINISH_TOOL}
        for tool in resolve_tools(tools if tools is not None else list(DEFAULT_TOOLS)):
            self.tools[tool.name] = tool

        # When permissions are set, replace bash with a sandboxed version
        if permissions and "bash" in self.tools:
            spec = _permissions_to_sandbox(permissions)
            self.tools["bash"] = sandboxed_bash_tool(spec)

    @classmethod
    def from_file(cls, path: str) -> "Agent":
        with open(path) as f:
            data = json.load(f)
        return cls(
            model=data.get("model", DEFAULT_MODEL),
            max_iterations=data.get("max_iterations", DEFAULT_MAX_ITERATIONS),
            tools=data.get("tools", list(DEFAULT_TOOLS)),
            permissions=data.get("permissions"),
        )

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
