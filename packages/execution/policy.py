from dataclasses import dataclass


@dataclass(frozen=True)
class SandboxPolicy:
    run_as_non_root: bool
    outbound_network_enabled: bool
    cpu_limit: int
    memory_limit_mb: int
    timeout_minutes: int
    approved_base_images_only: bool
    allow_user_dockerfiles: bool


def default_sandbox_policy() -> SandboxPolicy:
    return SandboxPolicy(
        run_as_non_root=True,
        outbound_network_enabled=False,
        cpu_limit=2,
        memory_limit_mb=4096,
        timeout_minutes=20,
        approved_base_images_only=True,
        allow_user_dockerfiles=False,
    )
