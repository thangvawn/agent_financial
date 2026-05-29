from __future__ import annotations

import re

from pydantic import BaseModel, Field, field_validator

_EMAIL_REGEX = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _validate_email(value: str) -> str:
    cleaned = value.strip().lower()
    if not _EMAIL_REGEX.match(cleaned):
        raise ValueError("Email không hợp lệ.")
    return cleaned


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=256)

    @field_validator("email")
    @classmethod
    def _email(cls, value: str) -> str:
        return _validate_email(value)


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=256)

    @field_validator("email")
    @classmethod
    def _email(cls, value: str) -> str:
        return _validate_email(value)


class GoogleLoginRequest(BaseModel):
    credential: str = Field(min_length=20, max_length=4096)


class LogoutRequest(BaseModel):
    session_id: str = Field(min_length=8, max_length=128)


class AccountProfile(BaseModel):
    email: str
    name: str
    session_mode: str = "server_account"


class AuthSessionResponse(BaseModel):
    session_id: str
    profile: AccountProfile


class AuthMeResponse(BaseModel):
    session_id: str
    profile: AccountProfile


class AuthLogoutResponse(BaseModel):
    status: str
