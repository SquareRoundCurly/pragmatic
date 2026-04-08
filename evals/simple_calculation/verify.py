"""Verify that result.txt contains the correct answer for 3^4."""

import sys
from pathlib import Path

EXPECTED = "81"


def main() -> int:
    result_file = Path(__file__).parent / "workspace" / "result.txt"
    if not result_file.exists():
        print("FAIL: result.txt not found")
        return 1

    actual = result_file.read_text().strip()
    if actual == EXPECTED:
        print("PASS")
        return 0

    print(f"FAIL: expected {EXPECTED}, got {actual!r}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
