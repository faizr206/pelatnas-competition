import bcrypt

from packages.auth.security import hash_password, verify_password


def test_hash_password_supports_long_passwords() -> None:
    password = "p" * 120

    password_hash = hash_password(password)

    assert verify_password(password, password_hash) is True
    assert verify_password("q" * 120, password_hash) is False


def test_verify_password_supports_legacy_raw_bcrypt_hashes() -> None:
    password = "legacy-password"
    legacy_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("ascii")

    assert verify_password(password, legacy_hash) is True
    assert verify_password("wrong-password", legacy_hash) is False
