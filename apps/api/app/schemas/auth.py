from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    display_name: str
    status: str
    is_admin: bool
    hide_from_leaderboard: bool
    must_change_password: bool


class LeaderboardVisibilityPreferenceRequest(BaseModel):
    hide_from_leaderboard: bool
