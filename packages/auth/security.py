import base64
import hashlib
import hmac
import re

import bcrypt

_BCRYPT_SHA256_V2_RE = re.compile(
    r"^\$bcrypt-sha256\$v=2,t=(?P<ident>2b),r=(?P<rounds>\d{1,2})\$(?P<salt>[^$]{22})\$(?P<checksum>[^$]{31})$"
)
_BCRYPT_SHA256_V1_RE = re.compile(
    r"^\$bcrypt-sha256\$(?P<ident>2[ab]),(?P<rounds>\d{1,2})\$(?P<salt>[^$]{22})\$(?P<checksum>[^$]{31})$"
)
_RAW_BCRYPT_SALT_RE = re.compile(r"^\$(?P<ident>2[abxy])\$(?P<rounds>\d{2})\$(?P<salt>[^$]{22})$")
_RAW_BCRYPT_RE = re.compile(
    r"^\$(?P<ident>2[abxy])\$(?P<rounds>\d{2})\$(?P<salt>[^$]{22})(?P<checksum>[^$]{31})$"
)


def hash_password(password: str) -> str:
    salt_hash = bcrypt.gensalt()
    raw_hash = salt_hash.decode("ascii")
    match = _RAW_BCRYPT_SALT_RE.match(raw_hash)
    if match is None:
        raise ValueError("Generated bcrypt salt has unexpected format.")

    ident = match.group("ident")
    rounds = int(match.group("rounds"))
    salt = match.group("salt")
    digest = _bcrypt_sha256_digest(password=password, salt=salt, version=2)
    checksum = _bcrypt_hash_digest(
        digest=digest,
        ident=ident,
        rounds=rounds,
        salt=salt,
    )
    return f"$bcrypt-sha256$v=2,t={ident},r={rounds}${salt}${checksum}"


def verify_password(password: str, password_hash: str) -> bool:
    for pattern, version in ((_BCRYPT_SHA256_V2_RE, 2), (_BCRYPT_SHA256_V1_RE, 1)):
        match = pattern.match(password_hash)
        if match is None:
            continue

        digest = _bcrypt_sha256_digest(
            password=password,
            salt=match.group("salt"),
            version=version,
        )
        return _check_bcrypt_hash(
            digest=digest,
            ident=match.group("ident"),
            rounds=int(match.group("rounds")),
            salt=match.group("salt"),
            checksum=match.group("checksum"),
        )

    if _RAW_BCRYPT_RE.match(password_hash):
        try:
            return bcrypt.checkpw(
                password.encode("utf-8"),
                password_hash.encode("ascii"),
            )
        except ValueError:
            return False

    return False


def _bcrypt_sha256_digest(*, password: str, salt: str, version: int) -> bytes:
    password_bytes = password.encode("utf-8")
    if version == 1:
        digest = hashlib.sha256(password_bytes).digest()
    else:
        digest = hmac.new(
            salt.encode("ascii"),
            password_bytes,
            hashlib.sha256,
        ).digest()
    return base64.b64encode(digest)


def _bcrypt_hash_digest(*, digest: bytes, ident: str, rounds: int, salt: str) -> str:
    raw_hash = bcrypt.hashpw(
        digest,
        f"${ident}${rounds:02d}${salt}".encode("ascii"),
    ).decode("ascii")
    match = _RAW_BCRYPT_RE.match(raw_hash)
    if match is None:
        raise ValueError("Generated bcrypt hash has unexpected format.")
    return match.group("checksum")


def _check_bcrypt_hash(
    *,
    digest: bytes,
    ident: str,
    rounds: int,
    salt: str,
    checksum: str,
) -> bool:
    try:
        return bcrypt.checkpw(
            digest,
            f"${ident}${rounds:02d}${salt}{checksum}".encode("ascii"),
        )
    except ValueError:
        return False
