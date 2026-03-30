from packages.execution.policy import SandboxPolicy, default_sandbox_policy


def current_resource_policy() -> SandboxPolicy:
    return default_sandbox_policy()
