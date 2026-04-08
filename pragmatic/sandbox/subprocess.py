"""Run a SandboxSpec via bubblewrap (bwrap)."""

import subprocess

from pragmatic.sandbox.spec import SandboxSpec


def build_bwrap_argv(spec: SandboxSpec) -> list[str]:
    argv = [
        "bwrap",
        "--die-with-parent",
        "--new-session",
        "--unshare-user",
        "--unshare-pid",
        "--unshare-uts",
        "--unshare-ipc",
    ]

    if not spec.share_net:
        argv.append("--unshare-net")

    argv += [
        "--ro-bind", "/usr", "/usr",
        "--ro-bind", "/bin", "/bin",
        "--ro-bind", "/lib", "/lib",
        "--ro-bind", "/lib64", "/lib64",
        "--proc", "/proc",
        "--dev", "/dev",
        "--tmpfs", "/tmp",
        "--clearenv",
        "--setenv", "PATH", "/usr/bin:/bin",
    ]

    for src, dst in spec.ro_binds:
        argv += ["--ro-bind", src, dst]

    for src, dst in spec.rw_binds:
        argv += ["--bind", src, dst]

    if spec.workdir:
        argv += ["--chdir", spec.workdir]

    for k, v in spec.env.items():
        argv += ["--setenv", k, v]

    argv += spec.command
    return argv


def run_spec(spec: SandboxSpec) -> subprocess.CompletedProcess:
    argv = build_bwrap_argv(spec)
    return subprocess.run(argv, check=True, text=True, capture_output=True)
