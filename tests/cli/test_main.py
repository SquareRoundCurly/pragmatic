"""Tests for pragmatic CLI entry point."""

import json
from unittest.mock import patch

import pytest

from pragmatic.__main__ import main

MOCK_RESPONSE = {
    "choices": [{"message": {"content": "Hello from LLM"}}]
}


class FakeResponse:
    def __init__(self):
        self.status_code = 200

    def raise_for_status(self):
        pass

    def json(self):
        return MOCK_RESPONSE


@pytest.fixture(autouse=True)
def set_api_key(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")


@pytest.fixture
def mock_post():
    with patch("pragmatic.__main__.requests.post", return_value=FakeResponse()) as m:
        yield m


def test_prompt_inline(mock_post, capsys, monkeypatch):
    monkeypatch.setattr("sys.argv", ["pragmatic", "--prompt", "hello"])
    main()
    assert capsys.readouterr().out.strip() == "Hello from LLM"
    assert mock_post.call_args[1]["json"]["messages"][0]["content"] == "hello"


def test_prompt_file(mock_post, capsys, monkeypatch, tmp_path):
    prompt_file = tmp_path / "prompt.txt"
    prompt_file.write_text("prompt from file")
    monkeypatch.setattr("sys.argv", ["pragmatic", "--prompt-file", str(prompt_file)])
    main()
    assert capsys.readouterr().out.strip() == "Hello from LLM"
    assert mock_post.call_args[1]["json"]["messages"][0]["content"] == "prompt from file"


def test_prompt_stdin(mock_post, capsys, monkeypatch):
    monkeypatch.setattr("sys.argv", ["pragmatic", "--prompt-file", "-"])
    monkeypatch.setattr("sys.stdin", __import__("io").StringIO("stdin prompt"))
    main()
    assert capsys.readouterr().out.strip() == "Hello from LLM"
    assert mock_post.call_args[1]["json"]["messages"][0]["content"] == "stdin prompt"


def test_output_to_file(mock_post, monkeypatch, tmp_path):
    output_file = tmp_path / "output.txt"
    monkeypatch.setattr("sys.argv", ["pragmatic", "--prompt", "hi", "--output", str(output_file)])
    main()
    assert output_file.read_text() == "Hello from LLM"


def test_custom_model(mock_post, capsys, monkeypatch):
    monkeypatch.setattr("sys.argv", ["pragmatic", "--prompt", "hi", "--model", "anthropic/claude-3"])
    main()
    assert mock_post.call_args[1]["json"]["model"] == "anthropic/claude-3"


def test_missing_api_key(monkeypatch, capsys):
    monkeypatch.delenv("OPENROUTER_API_KEY")
    monkeypatch.setattr("pragmatic.__main__.load_dotenv", lambda: None)
    monkeypatch.setattr("sys.argv", ["pragmatic", "--prompt", "hi"])
    with pytest.raises(SystemExit, match="1"):
        main()
    assert "OPENROUTER_API_KEY" in capsys.readouterr().err


def test_no_prompt_args_errors(monkeypatch):
    monkeypatch.setattr("sys.argv", ["pragmatic"])
    with pytest.raises(SystemExit, match="2"):
        main()


def test_both_prompt_args_errors(monkeypatch):
    monkeypatch.setattr("sys.argv", ["pragmatic", "--prompt", "hi", "--prompt-file", "f.txt"])
    with pytest.raises(SystemExit, match="2"):
        main()
