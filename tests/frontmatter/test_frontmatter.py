from pathlib import Path

from pragmatic.frontmatter import parse, dump

FIXTURES = Path(__file__).parent / "fixtures"


# --- inline tests ---


def test_parse_with_frontmatter():
    text = "---\ntitle: Hello\ntags:\n  - a\n  - b\n---\nBody content here."
    meta, content = parse(text)
    assert meta == {"title": "Hello", "tags": ["a", "b"]}
    assert content == "Body content here."


def test_parse_without_frontmatter():
    text = "Just plain text, no frontmatter."
    meta, content = parse(text)
    assert meta == {}
    assert content == text


def test_parse_unclosed_frontmatter():
    text = "---\ntitle: Oops\nNo closing delimiter."
    meta, content = parse(text)
    assert meta == {}
    assert content == text


def test_dump_with_meta():
    result = dump({"title": "Hi"}, "Body.")
    meta, content = parse(result)
    assert meta == {"title": "Hi"}
    assert content == "Body."


def test_dump_empty_meta():
    assert dump({}, "Body.") == "Body."


# --- file-based tests ---


def test_file_with_frontmatter():
    text = (FIXTURES / "with_frontmatter.md").read_text()
    meta, content = parse(text)
    assert meta == {"title": "Hello World", "author": "Alice", "tags": ["python", "testing"]}
    assert content.startswith("# Hello World")


def test_file_without_frontmatter():
    text = (FIXTURES / "without_frontmatter.md").read_text()
    meta, content = parse(text)
    assert meta == {}
    assert content.startswith("# Just a Heading")


def test_file_empty_frontmatter():
    text = (FIXTURES / "empty_frontmatter.md").read_text()
    meta, content = parse(text)
    assert meta == {}
    assert content == "Content after empty frontmatter.\n"
