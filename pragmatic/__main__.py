"""CLI entry point for pragmatic."""

import argparse
import json
import sys

from pragmatic.agent import Agent
from pragmatic.tools.bash import BASH_TOOL


def _read_prompt(args):
    if args.prompt_file:
        if args.prompt_file == "-":
            return sys.stdin.read()
        with open(args.prompt_file) as f:
            return f.read()
    return args.prompt


def main():
    parser = argparse.ArgumentParser(prog="pragmatic")
    parser.add_argument("--prompt", help="The prompt to send to the LLM")
    parser.add_argument("--prompt-file", help="Read prompt from a file (- for stdin)")
    parser.add_argument("--output", help="Write output to a file instead of stdout")
    parser.add_argument("--model", default="openai/gpt-4.1-nano", help="OpenRouter model to use")
    parser.add_argument("--max-iterations", type=int, default=10, help="Max agent loop iterations (default: 10)")
    args = parser.parse_args()

    if args.prompt and args.prompt_file:
        parser.error("--prompt and --prompt-file are mutually exclusive")
    if not args.prompt and not args.prompt_file:
        parser.error("one of --prompt or --prompt-file is required")

    prompt = _read_prompt(args)

    agent = Agent(model=args.model, tools=[BASH_TOOL], max_iterations=args.max_iterations)
    result = agent.run(prompt)
    output = json.dumps(result, indent=2)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
    else:
        print(output)


if __name__ == "__main__":
    main()
