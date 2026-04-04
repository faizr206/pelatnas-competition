from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from apps.api.app.dependencies.auth import get_admin_user
from apps.api.app.dependencies.db import get_db
from apps.api.app.repositories.users import get_user_by_email, get_user_by_id, list_users
from apps.api.app.schemas.users import (
    AdminPasswordResetRequest,
    AdminUserCreateRequest,
    AdminUserResponse,
    AdminUserUpdateRequest,
)
from apps.api.app.services.auth import change_user_password, validate_new_password
from packages.db.models import User

router = APIRouter(prefix="/admin/users", tags=["users"])


@router.get("", response_model=list[AdminUserResponse])
def get_users(
    _: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> list[AdminUserResponse]:
    return [AdminUserResponse.model_validate(user) for user in list_users(db)]


@router.post("", response_model=AdminUserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: AdminUserCreateRequest,
    _: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> AdminUserResponse:
    existing_user = get_user_by_email(db, email=payload.email)
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )

    validate_new_password(new_password=payload.default_password)
    user = User(
        email=payload.email.lower(),
        display_name=payload.display_name.strip(),
        password_hash="",
        status=payload.status,
        is_admin=payload.is_admin,
        must_change_password=True,
    )
    change_user_password(user, new_password=payload.default_password, require_password_change=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    return AdminUserResponse.model_validate(user)


@router.patch("/{user_id}", response_model=AdminUserResponse)
def update_user(
    user_id: str,
    payload: AdminUserUpdateRequest,
    current_admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> AdminUserResponse:
    user = get_user_by_id(db, user_id=user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if current_admin.id == user.id and not payload.is_admin:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="You cannot remove your own admin access.",
        )

    user.display_name = payload.display_name.strip()
    user.status = payload.status
    user.is_admin = payload.is_admin
    db.add(user)
    db.commit()
    db.refresh(user)
    return AdminUserResponse.model_validate(user)


@router.post("/{user_id}/reset-password", response_model=AdminUserResponse)
def reset_user_password(
    user_id: str,
    payload: AdminPasswordResetRequest,
    current_admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> AdminUserResponse:
    user = get_user_by_id(db, user_id=user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if current_admin.id == user.id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Use the profile page to change your own password.",
        )

    validate_new_password(new_password=payload.default_password)
    change_user_password(user, new_password=payload.default_password, require_password_change=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    return AdminUserResponse.model_validate(user)
