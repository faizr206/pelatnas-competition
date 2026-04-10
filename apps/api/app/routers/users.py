import csv
from io import StringIO

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from apps.api.app.config import get_settings
from apps.api.app.dependencies.auth import get_admin_user
from apps.api.app.dependencies.db import get_db
from apps.api.app.repositories.users import get_user_by_email, get_user_by_id, list_users
from apps.api.app.schemas.users import (
    AdminBulkUserImportResponse,
    AdminPasswordResetRequest,
    AdminUserCreateRequest,
    AdminUserResponse,
    AdminUserUpdateRequest,
)
from apps.api.app.services.auth import change_user_password, validate_new_password
from packages.db.models import User
from packages.security.upload_validation import validate_csv_upload, validate_upload_size

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


@router.post(
    "/import",
    response_model=AdminBulkUserImportResponse,
    status_code=status.HTTP_201_CREATED,
)
def import_users(
    csv_file: UploadFile = File(...),
    _: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> AdminBulkUserImportResponse:
    settings = get_settings()
    validate_upload_size(
        csv_file,
        max_bytes=settings.max_solution_upload_bytes,
        label="user import file",
    )
    validate_csv_upload(csv_file, label="user import file")

    csv_file.file.seek(0)
    try:
        payload = csv_file.file.read().decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User import file must be valid UTF-8 text.",
        ) from exc

    reader = csv.DictReader(StringIO(payload))
    if reader.fieldnames is None:
        raise HTTPException(status_code=400, detail="User import CSV must include a header row.")

    expected_headers = {"display_name", "email", "default_password"}
    actual_headers = {field.strip() for field in reader.fieldnames if field}
    if actual_headers != expected_headers:
        raise HTTPException(
            status_code=400,
            detail="User import CSV must contain exactly: display_name,email,default_password",
        )

    created_users: list[User] = []
    seen_emails: set[str] = set()
    for index, row in enumerate(reader, start=2):
        normalized_row = {key.strip(): (value or "").strip() for key, value in row.items() if key}
        try:
            user_payload = AdminUserCreateRequest(
                email=normalized_row.get("email", ""),
                display_name=normalized_row.get("display_name", ""),
                default_password=normalized_row.get("default_password", ""),
                is_admin=False,
                status="active",
            )
        except ValidationError as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid user import row {index}: {exc.errors()[0]['msg']}",
            ) from exc

        normalized_email = user_payload.email.lower()
        if normalized_email in seen_emails:
            raise HTTPException(
                status_code=409,
                detail=f"Duplicate email in user import CSV at row {index}: {normalized_email}",
            )
        if get_user_by_email(db, email=normalized_email) is not None:
            raise HTTPException(
                status_code=409,
                detail=f"A user with email {normalized_email} already exists.",
            )

        validate_new_password(new_password=user_payload.default_password)
        user = User(
            email=normalized_email,
            display_name=user_payload.display_name.strip(),
            password_hash="",
            status="active",
            is_admin=False,
            must_change_password=True,
        )
        change_user_password(
            user,
            new_password=user_payload.default_password,
            require_password_change=True,
        )
        db.add(user)
        created_users.append(user)
        seen_emails.add(normalized_email)

    if not created_users:
        raise HTTPException(
            status_code=400, detail="User import CSV must include at least one row."
        )

    db.commit()
    for user in created_users:
        db.refresh(user)
    return AdminBulkUserImportResponse(
        created_count=len(created_users),
        users=[AdminUserResponse.model_validate(user) for user in created_users],
    )


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
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
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
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Use the profile page to change your own password.",
        )

    validate_new_password(new_password=payload.default_password)
    change_user_password(user, new_password=payload.default_password, require_password_change=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    return AdminUserResponse.model_validate(user)
