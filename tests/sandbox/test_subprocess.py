"""Tests for sandbox subprocess (bwrap argv building)."""

from pragmatic.sandbox.spec import SandboxSpec
from pragmatic.sandbox.subprocess import build_bwrap_argv


def test_minimal_argv():
    spec = SandboxSpec(command=["echo", "hello"])
    argv = build_bwrap_argv(spec)

    assert argv[0] == "bwrap"
    assert "--die-with-parent" in argv
    assert "--unshare-net" in argv
    assert argv[-2:] == ["echo", "hello"]


def test_share_net_omits_unshare_net():
    spec = SandboxSpec(command=["true"], share_net=True)
    argv = build_bwrap_argv(spec)

    assert "--unshare-net" not in argv


def test_ro_binds():
    spec = SandboxSpec(command=["true"], ro_binds=[("/src", "/mnt/src")])
    argv = build_bwrap_argv(spec)

    idx = argv.index("--ro-bind")
    # The last --ro-bind should be our custom one (after the system ones)
    last_ro = len(argv) - 1 - argv[::-1].index("--ro-bind")
    assert argv[last_ro + 1] == "/src"
    assert argv[last_ro + 2] == "/mnt/src"


def test_rw_binds():
    spec = SandboxSpec(command=["true"], rw_binds=[("/data", "/data")])
    argv = build_bwrap_argv(spec)

    idx = argv.index("--bind")
    assert argv[idx + 1] == "/data"
    assert argv[idx + 2] == "/data"


def test_workdir():
    spec = SandboxSpec(command=["ls"], workdir="/app")
    argv = build_bwrap_argv(spec)

    idx = argv.index("--chdir")
    assert argv[idx + 1] == "/app"


def test_no_workdir():
    spec = SandboxSpec(command=["ls"])
    argv = build_bwrap_argv(spec)

    assert "--chdir" not in argv


def test_env_vars():
    spec = SandboxSpec(command=["env"], env={"FOO": "bar", "BAZ": "qux"})
    argv = build_bwrap_argv(spec)

    # Find our custom --setenv entries (after the PATH one)
    setenv_indices = [i for i, v in enumerate(argv) if v == "--setenv"]
    # At least PATH + our 2 custom vars
    assert len(setenv_indices) >= 3

    # Check our vars are present
    joined = " ".join(argv)
    assert "--setenv FOO bar" in joined
    assert "--setenv BAZ qux" in joined


def test_clearenv_present():
    spec = SandboxSpec(command=["true"])
    argv = build_bwrap_argv(spec)

    assert "--clearenv" in argv


def test_system_ro_binds():
    spec = SandboxSpec(command=["true"])
    argv = build_bwrap_argv(spec)

    joined = " ".join(argv)
    for path in ["/usr", "/bin", "/lib", "/lib64"]:
        assert f"--ro-bind {path} {path}" in joined


def test_command_is_last():
    spec = SandboxSpec(
        command=["bash", "-c", "echo test"],
        workdir="/tmp",
        env={"X": "1"},
        ro_binds=[("/a", "/b")],
        rw_binds=[("/c", "/d")],
    )
    argv = build_bwrap_argv(spec)

    assert argv[-3:] == ["bash", "-c", "echo test"]
