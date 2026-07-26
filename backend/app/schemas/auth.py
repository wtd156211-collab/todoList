from uuid import UUID

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    code: str | None = Field(default=None, min_length=1)
    refresh_token: str | None = Field(default=None, alias="refreshToken", min_length=1)


class UserResponse(BaseModel):
    id: UUID
    openid: str


class TokenResponse(BaseModel):
    access_token: str = Field(alias="accessToken")
    refresh_token: str = Field(alias="refreshToken")
    user: UserResponse
