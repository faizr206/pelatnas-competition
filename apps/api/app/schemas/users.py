from pydantic import BaseModel, ConfigDict, EmailStr, Field

from apps.api.app.schemas.auth import UserResponse


class AdminUserCreateRequest(BaseModel):
    email: EmailStr
    display_name: str = Field(min_length=1, max_length=255)
    default_password: str = Field(min_length=8, max_length=128)
    is_admin: bool = False
    status: str = Field(default="active", pattern="^(active|suspended)$")


class AdminUserUpdateRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=255)
    is_admin: bool
    status: str = Field(pattern="^(active|suspended)$")


class AdminPasswordResetRequest(BaseModel):
    default_password: str = Field(min_length=8, max_length=128)


class AdminUserResponse(UserResponse):
    model_config = ConfigDict(from_attributes=True)
