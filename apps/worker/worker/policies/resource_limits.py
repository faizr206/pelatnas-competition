from packages.db.models import Competition
from packages.execution.policy import SandboxPolicy, default_sandbox_policy


def current_resource_policy() -> SandboxPolicy:
    return default_sandbox_policy()


def competition_resource_policy(competition: Competition) -> SandboxPolicy:
    return SandboxPolicy(
        run_as_non_root=True,
        outbound_network_enabled=False,
        cpu_limit=competition.max_cpu,
        memory_limit_mb=competition.max_memory_mb,
        timeout_minutes=competition.max_runtime_minutes,
        approved_base_images_only=True,
        allow_user_dockerfiles=False,
    )
