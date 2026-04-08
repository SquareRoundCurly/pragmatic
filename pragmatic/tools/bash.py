"""Bash tool — executes shell commands via subprocess."""

import json
import subprocess

from pragmatic.tools import Tool


def _bash_handler(command: str) -> str:
    result = subprocess.run(
        ["bash", "-c", command],
        capture_output=True,
        text=True,
        timeout=30,
    )
    return json.dumps({
        "stdout": result.stdout,
        "stderr": result.stderr,
        "exit_code": result.returncode,
    })


BASH_TOOL = Tool(
    name="bash",
    description="Execute a bash command and return its stdout, stderr, and exit code.",
    parameters={
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The bash command to execute.",
            },
        },
        "required": ["command"],
    },
    handler=_bash_handler,
)
