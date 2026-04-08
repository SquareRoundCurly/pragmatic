"""Shared fixtures for integration tests."""

import subprocess

import pytest


def _bwrap_available() -> bool:
    try:
        result = subprocess.run(
            ["bwrap", "--ro-bind", "/usr", "/usr", "--ro-bind", "/bin", "/bin",
             "--ro-bind", "/lib", "/lib", "--ro-bind", "/lib64", "/lib64",
             "--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp",
             "--unshare-pid", "--die-with-parent", "true"],
            capture_output=True, timeout=5,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


requires_bwrap = pytest.mark.skipif(
    not _bwrap_available(),
    reason="bwrap not available or user namespaces disabled",
)
