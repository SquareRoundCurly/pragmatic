"""Run all eval cases found under evals/."""

import subprocess
import sys
from pathlib import Path

EVALS_DIR = Path(__file__).parent


def _find_prompt(case_dir: Path) -> Path | None:
    """Find prompt.md in the case dir or its workspace subdir."""
    for candidate in [case_dir / "workspace" / "prompt.md", case_dir / "prompt.md"]:
        if candidate.exists():
            return candidate
    return None


def discover_cases() -> list[Path]:
    return sorted(
        d for d in EVALS_DIR.iterdir()
        if d.is_dir() and _find_prompt(d) and (d / "verify.py").exists()
    )


def cleanup_case(case_dir: Path) -> None:
    cleanup = case_dir / "cleanup.py"
    if cleanup.exists():
        subprocess.run(
            [sys.executable, "cleanup.py"],
            cwd=case_dir,
            timeout=30,
        )


def run_case(case_dir: Path) -> bool:
    name = case_dir.name
    print(f"=== {name} ===")

    # Run pragmatic with the prompt, cwd set to the case dir
    prompt_path = _find_prompt(case_dir)
    cmd = [sys.executable, "-m", "pragmatic", "--prompt-file", str(prompt_path.relative_to(case_dir))]
    agent_json = case_dir / "agent.json"
    if agent_json.exists():
        cmd += ["--agent", "agent.json"]
    result = subprocess.run(
        cmd,
        cwd=case_dir,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        print(f"  FAIL: pragmatic exited with {result.returncode}")
        print(f"  stderr: {result.stderr.strip()}")
        return False

    # Run verify.py
    verify = subprocess.run(
        [sys.executable, "verify.py"],
        cwd=case_dir,
        capture_output=True,
        text=True,
        timeout=30,
    )
    output = verify.stdout.strip()
    print(f"  {output}")
    return verify.returncode == 0


def main() -> int:
    cases = discover_cases()
    if not cases:
        print("No eval cases found")
        return 1

    # Cleanup all cases before running
    for case in cases:
        cleanup_case(case)

    results = {case.name: run_case(case) for case in cases}

    print()
    passed = sum(results.values())
    total = len(results)
    print(f"{passed}/{total} evals passed")

    if passed < total:
        for name, ok in results.items():
            if not ok:
                print(f"  FAILED: {name}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
