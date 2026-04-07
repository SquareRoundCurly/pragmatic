"""CLI entry point for pragmatic."""

import argparse
import os
import sys

from dotenv import load_dotenv
from openrouter import OpenRouter
from openrouter.components import ChatUserMessage


def main():
    load_dotenv()
    parser = argparse.ArgumentParser(prog="pragmatic")
    parser.add_argument("--prompt", help="The prompt to send to the LLM")
    parser.add_argument("--prompt-file", help="Read prompt from a file (- for stdin)")
    parser.add_argument("--output", help="Write output to a file instead of stdout")
    parser.add_argument("--model", default="openai/gpt-4.1-nano", help="OpenRouter model to use")
    args = parser.parse_args()

    if args.prompt and args.prompt_file:
        parser.error("--prompt and --prompt-file are mutually exclusive")
    if not args.prompt and not args.prompt_file:
        parser.error("one of --prompt or --prompt-file is required")

    if args.prompt_file:
        if args.prompt_file == "-":
            prompt = sys.stdin.read()
        else:
            with open(args.prompt_file) as f:
                prompt = f.read()
    else:
        prompt = args.prompt

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    client = OpenRouter(api_key=api_key)
    response = client.chat.send(
        model=args.model,
        messages=[ChatUserMessage(role="user", content=prompt)],
    )

    content = response.choices[0].message.content

    if args.output:
        with open(args.output, "w") as f:
            f.write(content)
    else:
        print(content)


if __name__ == "__main__":
    main()
