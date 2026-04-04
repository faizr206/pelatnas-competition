from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from apps.api.app.config import get_settings
from apps.api.app.dependencies.auth import get_current_user
from apps.api.app.dependencies.db import get_db
from apps.api.app.schemas.auth import ChangePasswordRequest, LoginRequest, UserResponse
from apps.api.app.services.auth import (
    authenticate_user,
    change_user_password,
    validate_new_password,
)
from packages.db.models import User
from packages.security.login_rate_limit import login_rate_limiter

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=UserResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> UserResponse:
    settings = get_settings()
    client_host = request.client.host if request.client is not None else "unknown"
    limit_key = f"{payload.email.lower()}:{client_host}"
    limit_status = login_rate_limiter.check(
        key=limit_key,
        window_seconds=settings.login_rate_limit_window_seconds,
        max_attempts=settings.login_rate_limit_max_attempts,
    )
    if limit_status.limited:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Try again later.",
            headers={"Retry-After": str(limit_status.retry_after_seconds)},
        )

    user = authenticate_user(db, email=payload.email, password=payload.password)
    if user is None:
        login_rate_limiter.record_failure(
            key=limit_key,
            window_seconds=settings.login_rate_limit_window_seconds,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    login_rate_limiter.clear(key=limit_key)
    request.session["user_id"] = user.id
    return UserResponse.model_validate(user)


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.post("/change-password", response_model=UserResponse)
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    user = authenticate_user(
        db,
        email=current_user.email,
        password=payload.current_password,
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect.",
        )

    validate_new_password(
        new_password=payload.new_password,
        current_password=payload.current_password,
    )
    change_user_password(user, new_password=payload.new_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request) -> Response:
    request.session.clear()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
