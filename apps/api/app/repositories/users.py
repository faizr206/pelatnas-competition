from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.db.models import User


def get_user_by_email(db: Session, *, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.lower()))


def get_user_by_id(db: Session, *, user_id: str) -> User | None:
    return db.scalar(select(User).where(User.id == user_id))
