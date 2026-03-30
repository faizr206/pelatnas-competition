from packages.auth.security import hash_password, verify_password


def test_hash_password_supports_long_passwords() -> None:
    password = "p" * 120

    password_hash = hash_password(password)

    assert verify_password(password, password_hash) is True
    assert verify_password("q" * 120, password_hash) is False

