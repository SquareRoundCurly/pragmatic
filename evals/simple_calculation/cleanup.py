"""Remove result.txt if it exists."""

from pathlib import Path

result_file = Path(__file__).parent / "workspace" / "result.txt"
if result_file.exists():
    result_file.unlink()
