"""Sandbox specification."""

from dataclasses import dataclass, field


@dataclass
class SandboxSpec:
    command: list[str]
    workdir: str | None = None
    ro_binds: list[tuple[str, str]] = field(default_factory=list)
    rw_binds: list[tuple[str, str]] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    share_net: bool = False
