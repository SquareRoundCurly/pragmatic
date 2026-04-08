"""Bash tool — executes shell commands via subprocess."""

import json
import subprocess

from pragmatic.sandbox.spec import SandboxSpec
from pragmatic.sandbox.subprocess import build_bwrap_argv
from pragmatic.tools import Tool

_BASH_PARAMETERS = {
    "type": "object",
    "properties": {
        "command": {
            "type": "string",
            "description": "The bash command to execute.",
        },
    },
    "required": ["command"],
}


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


def _sandboxed_bash_handler(spec_base: SandboxSpec):
    """Return a bash handler that runs commands inside a bwrap sandbox."""
    def handler(command: str) -> str:
        spec = SandboxSpec(
            command=["bash", "-c", command],
            workdir=spec_base.workdir,
            ro_binds=list(spec_base.ro_binds),
            rw_binds=list(spec_base.rw_binds),
            env=dict(spec_base.env),
            share_net=spec_base.share_net,
        )
        argv = build_bwrap_argv(spec)
        result = subprocess.run(argv, capture_output=True, text=True, timeout=30)
        return json.dumps({
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
        })
    return handler


def sandboxed_bash_tool(spec: SandboxSpec) -> Tool:
    """Create a bash tool that runs inside a bwrap sandbox."""
    return Tool(
        name="bash",
        description="Execute a bash command and return its stdout, stderr, and exit code.",
        parameters=_BASH_PARAMETERS,
        handler=_sandboxed_bash_handler(spec),
    )


BASH_TOOL = Tool(
    name="bash",
    description="Execute a bash command and return its stdout, stderr, and exit code.",
    parameters=_BASH_PARAMETERS,
    handler=_bash_handler,
)
