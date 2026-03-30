from sqlalchemy.orm import Session

from apps.api.app.repositories.users import get_user_by_email
from packages.auth.security import verify_password
from packages.db.models import User


def authenticate_user(db: Session, *, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email=email)
    if user is None:
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user
