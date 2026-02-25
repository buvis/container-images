import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str = ""

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    password: str

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    email: str
    name: str
    is_active: bool
    locale: str
    timezone: str
    default_vault_id: uuid.UUID | None
    created_at: datetime


class AuthResponse(BaseModel):
    user: UserRead
    access_token: str
    vault_id: uuid.UUID | None


class TwoFactorChallengeResponse(BaseModel):
    requires_2fa: bool
    temp_token: str


class TwoFactorSetupResponse(BaseModel):
    provisioning_uri: str
    qr_data_url: str
    recovery_codes: list[str]


class TwoFactorVerifyRequest(BaseModel):
    temp_token: str
    code: str


class TwoFactorConfirmRequest(BaseModel):
    code: str


LoginResponse = AuthResponse | TwoFactorChallengeResponse


class MemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_id: uuid.UUID
    email: str
    name: str
    role: str
    joined_at: datetime


class MemberInvite(BaseModel):
    email: EmailStr
    role: Literal["owner", "admin", "member"] = "member"


class MemberUpdate(BaseModel):
    role: Literal["owner", "admin", "member"]


class PatCreate(BaseModel):
    name: str
    scopes: list[str] = ["read", "write"]
    expires_in_days: int | None = None


class PatRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    token_prefix: str
    scopes: list[str]
    expires_at: datetime | None
    last_used_at: datetime | None
    created_at: datetime


class PatCreateResponse(PatRead):
    token: str


class VaultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    created_at: datetime


class VaultCreate(BaseModel):
    name: str


class VaultUpdate(BaseModel):
    name: str | None = None


class VaultSettingsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    vault_id: uuid.UUID
    language: str
    date_format: str
    time_format: str
    timezone: str
    feature_flags: dict[str, bool]


class VaultSettingsUpdate(BaseModel):
    language: str | None = None
    date_format: str | None = None
    time_format: str | None = None
    timezone: str | None = None
    feature_flags: dict[str, bool] | None = None
