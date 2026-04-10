from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from apps.api.app.dependencies.db import get_db
from apps.api.app.repositories.users import get_user_by_id
from packages.db.models import User


def get_optional_current_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None

    user = get_user_by_id(db, user_id=user_id)
    if user is None or user.status != "active":
        request.session.clear()
        return None

    return user


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    user = get_optional_current_user(request, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.")

    return user


def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required.")
    return current_user
