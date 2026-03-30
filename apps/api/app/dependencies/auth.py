from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from apps.api.app.dependencies.db import get_db
from apps.api.app.repositories.users import get_user_by_id
from packages.db.models import User


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.")

    user = get_user_by_id(db, user_id=user_id)
    if user is None:
        request.session.clear()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session is invalid.")

    return user
