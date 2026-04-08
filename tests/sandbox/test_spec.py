"""Tests for SandboxSpec."""

from pragmatic.sandbox.spec import SandboxSpec


def test_defaults():
    spec = SandboxSpec(command=["echo", "hi"])
    assert spec.command == ["echo", "hi"]
    assert spec.workdir is None
    assert spec.ro_binds == []
    assert spec.rw_binds == []
    assert spec.env == {}
    assert spec.share_net is False


def test_custom_fields():
    spec = SandboxSpec(
        command=["ls"],
        workdir="/tmp",
        ro_binds=[("/src", "/src")],
        rw_binds=[("/data", "/data")],
        env={"FOO": "bar"},
        share_net=True,
    )
    assert spec.workdir == "/tmp"
    assert spec.ro_binds == [("/src", "/src")]
    assert spec.rw_binds == [("/data", "/data")]
    assert spec.env == {"FOO": "bar"}
    assert spec.share_net is True
