from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from apps.api.app.repositories.users import get_user_by_email
from packages.auth.security import hash_password, verify_password
from packages.core.time import utcnow
from packages.db.models import User


def authenticate_user(db: Session, *, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email=email)
    if user is None:
        return None

    if not verify_password(password, user.password_hash):
        return None

    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is not active.",
        )

    return user


def validate_new_password(*, new_password: str, current_password: str | None = None) -> None:
    if len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="New password must be at least 8 characters long.",
        )

    if current_password is not None and new_password == current_password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="New password must be different from the current password.",
        )


def change_user_password(
    user: User,
    *,
    new_password: str,
    require_password_change: bool = False,
) -> None:
    user.password_hash = hash_password(new_password)
    user.must_change_password = require_password_change
    user.password_changed_at = utcnow()
