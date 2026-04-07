"""Integration tests for pragmatic CLI."""

import io
import subprocess
import sys

import pytest


def run_cli(*args):
    result = subprocess.run(
        [sys.executable, "-m", "pragmatic", *args],
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result


def test_prompt_inline():
    r = run_cli("--prompt", "Reply with exactly: PONG")
    assert r.returncode == 0
    assert len(r.stdout.strip()) > 0


def test_prompt_file(tmp_path):
    prompt_file = tmp_path / "prompt.txt"
    prompt_file.write_text("Reply with exactly: PONG")
    r = run_cli("--prompt-file", str(prompt_file))
    assert r.returncode == 0
    assert len(r.stdout.strip()) > 0


def test_prompt_stdin():
    result = subprocess.run(
        [sys.executable, "-m", "pragmatic", "--prompt-file", "-"],
        input="Reply with exactly: PONG",
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0
    assert len(result.stdout.strip()) > 0


def test_output_to_file(tmp_path):
    output_file = tmp_path / "output.txt"
    r = run_cli("--prompt", "Reply with exactly: PONG", "--output", str(output_file))
    assert r.returncode == 0
    assert output_file.exists()
    assert len(output_file.read_text()) > 0


def test_custom_model():
    r = run_cli("--prompt", "Reply with exactly: PONG", "--model", "openai/gpt-4.1-nano")
    assert r.returncode == 0
    assert len(r.stdout.strip()) > 0


def test_missing_api_key(tmp_path):
    result = subprocess.run(
        [sys.executable, "-c",
         "import os; os.chdir('/tmp');"
         "from pragmatic.__main__ import main;"
         "import sys; sys.argv=['pragmatic','--prompt','hi'];"
         "main()"],
        capture_output=True,
        text=True,
        timeout=10,
        env={"PATH": subprocess.os.environ["PATH"], "HOME": str(tmp_path)},
        cwd=str(tmp_path),
    )
    assert result.returncode == 1
    assert "OPENROUTER_API_KEY" in result.stderr


def test_no_prompt_args_errors():
    r = run_cli()
    assert r.returncode == 2


def test_both_prompt_args_errors():
    r = run_cli("--prompt", "hi", "--prompt-file", "f.txt")
    assert r.returncode == 2
