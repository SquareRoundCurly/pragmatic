"""Parse and dump YAML frontmatter from text."""

import yaml


def parse(text: str) -> tuple[dict, str]:
    """Parse frontmatter from text. Returns (metadata, content)."""
    if not text.startswith("---"):
        return {}, text

    end = text.find("---", 3)
    if end == -1:
        return {}, text

    raw = text[3:end].strip()
    meta = yaml.safe_load(raw) or {}
    content = text[end + 3:].lstrip("\n")
    return meta, content


def dump(meta: dict, content: str = "") -> str:
    """Dump metadata and content into a frontmatter string."""
    if not meta:
        return content
    front = yaml.dump(meta, default_flow_style=False).strip()
    return f"---\n{front}\n---\n{content}"
