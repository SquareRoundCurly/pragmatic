"""CLI entry point for pragmatic."""

import argparse
import os
import sys

import requests
from dotenv import load_dotenv


def main():
    load_dotenv()
    parser = argparse.ArgumentParser(prog="pragmatic")
    parser.add_argument("--prompt", required=True, help="The prompt to send to the LLM")
    parser.add_argument("--model", default="openai/gpt-4.1-nano", help="OpenRouter model to use")
    args = parser.parse_args()

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": args.model,
            "messages": [{"role": "user", "content": args.prompt}],
        },
    )
    response.raise_for_status()

    print(response.json()["choices"][0]["message"]["content"])


if __name__ == "__main__":
    main()
