"""Finish tool — signals task completion."""

import json

from pragmatic.tools import Tool


def _finish_handler(success: bool, reason: str) -> str:
    return json.dumps({"success": success, "reason": reason})


FINISH_TOOL = Tool(
    name="finish",
    description="Call this tool when the task is complete or cannot be completed.",
    parameters={
        "type": "object",
        "properties": {
            "success": {
                "type": "boolean",
                "description": "Whether the task was completed successfully.",
            },
            "reason": {
                "type": "string",
                "description": "Explanation of why the task finished.",
            },
        },
        "required": ["success", "reason"],
    },
    handler=_finish_handler,
)
