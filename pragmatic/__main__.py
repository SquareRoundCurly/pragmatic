"""CLI entry point for pragmatic."""

import argparse
import os
import sys

import requests
from dotenv import load_dotenv


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

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": args.model,
            "messages": [{"role": "user", "content": prompt}],
        },
    )
    response.raise_for_status()

    content = response.json()["choices"][0]["message"]["content"]

    if args.output:
        with open(args.output, "w") as f:
            f.write(content)
    else:
        print(content)


if __name__ == "__main__":
    main()
