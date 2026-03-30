from packages.execution.policy import default_sandbox_policy


def test_default_sandbox_policy_matches_phase_zero_limits() -> None:
    policy = default_sandbox_policy()

    assert policy.run_as_non_root is True
    assert policy.outbound_network_enabled is False
    assert policy.cpu_limit == 2
    assert policy.memory_limit_mb == 4096
    assert policy.timeout_minutes == 20
    assert policy.approved_base_images_only is True
    assert policy.allow_user_dockerfiles is False
