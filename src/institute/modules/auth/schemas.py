import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator


class UserCreate(BaseModel):
    """DTO to create a user. Received in the request."""

    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v


class UserResponse(BaseModel):
    """DTO to return a user. NEVER includes the password."""

    id: uuid.UUID
    email: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """DTO to return the JWT token."""

    access_token: str
    token_type: str = "bearer"  # noqa: S105 — OAuth2 token type, not a password
    expires_in: int  # seconds


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
