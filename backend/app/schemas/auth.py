"""Pydantic schemas for auth requests and responses."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from backend.app.models.user import UserRole


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    # 128 chars is generous for a real password; bcrypt silently truncates at 72
    # bytes so we cap before that ambiguity matters.
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def password_not_trivial(cls, v: str) -> str:
        if v.isdigit() or v.isalpha():
            raise ValueError(
                "Password must contain a mix of letters and numbers or special characters."
            )
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    # min_length=1 prevents empty-string bypass; max_length=128 matches
    # RegisterRequest so bcrypt's 72-byte truncation is consistently pre-empted.
    password: str = Field(min_length=1, max_length=128)


# ---------------------------------------------------------------------------
# Responses — never include password_hash, hashing parameters, or role source
# ---------------------------------------------------------------------------

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: UserRole
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
