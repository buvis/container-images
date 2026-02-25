import base64
import io
import logging
import secrets
import string
import uuid
from datetime import UTC, datetime
from typing import Annotated

import pyotp
import qrcode
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import delete, select

from clara.auth.models import PersonalAccessToken, RecoveryCode, TotpDevice, User
from clara.auth.schemas import (
    AuthResponse,
    ForgotPasswordRequest,
    LoginRequest,
    LoginResponse,
    PatCreate,
    PatCreateResponse,
    PatRead,
    RegisterRequest,
    ResetPasswordRequest,
    TwoFactorChallengeResponse,
    TwoFactorConfirmRequest,
    TwoFactorSetupResponse,
    TwoFactorVerifyRequest,
    UserRead,
)
from clara.auth.security import (
    create_access_token,
    create_refresh_token,
    create_reset_token,
    decode_2fa_temp_token,
    decode_access_token,
    decode_refresh_token,
    decode_reset_token,
    decrypt_totp_secret,
    encrypt_totp_secret,
    hash_password,
    verify_password,
)
from clara.auth.service import AuthService
from clara.config import get_settings
from clara.deps import CurrentUser, Db
from clara.middleware import generate_csrf_token
from clara.redis import blacklist_token, get_async_redis

router = APIRouter()
logger = logging.getLogger(__name__)


def get_auth_service(db: Db) -> AuthService:
    return AuthService(db)


AuthSvc = Annotated[AuthService, Depends(get_auth_service)]

LOGIN_RATE_LIMIT = 5
LOGIN_RATE_WINDOW = 60  # seconds

REGISTER_RATE_LIMIT = 3
REGISTER_RATE_WINDOW = 3600  # 1 hour


async def _check_login_rate(request: Request) -> None:
    ip = request.client.host if request.client else "unknown"
    key = f"rate:login:{ip}"
    r = get_async_redis()
    count = await r.incr(key)
    if count == 1:
        await r.expire(key, LOGIN_RATE_WINDOW)
    if count > LOGIN_RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Too many login attempts")


async def _check_register_rate(request: Request) -> None:
    ip = request.client.host if request.client else "unknown"
    key = f"rate:register:{ip}"
    r = get_async_redis()
    count = await r.incr(key)
    if count == 1:
        await r.expire(key, REGISTER_RATE_WINDOW)
    if count > REGISTER_RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Too many registration attempts")


def _set_auth_cookies(response: Response, access: str, refresh: str) -> None:
    settings = get_settings()
    for name, value, max_age in [
        ("access_token", access, settings.access_token_expire_minutes * 60),
        ("refresh_token", refresh, settings.refresh_token_expire_days * 86400),
    ]:
        response.set_cookie(
            key=name,
            value=value,
            max_age=max_age,
            httponly=settings.cookie_httponly,
            secure=settings.cookie_secure,
            samesite=settings.cookie_samesite,
            domain=settings.cookie_domain,
        )
    # CSRF token — readable by JS (httponly=False)
    response.set_cookie(
        key="csrf_token",
        value=generate_csrf_token(access),
        max_age=settings.access_token_expire_minutes * 60,
        httponly=False,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        domain=settings.cookie_domain,
    )


@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(
    body: RegisterRequest, svc: AuthSvc, response: Response, request: Request
) -> AuthResponse:
    await _check_register_rate(request)
    user, vault, access, refresh = await svc.register(body)
    _set_auth_cookies(response, access, refresh)
    return AuthResponse(
        user=UserRead.model_validate(user),
        access_token=access,
        vault_id=vault.id,
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    svc: AuthSvc,
    response: Response,
    request: Request,
) -> AuthResponse | TwoFactorChallengeResponse:
    await _check_login_rate(request)
    result = await svc.login(body)
    if result.requires_2fa:
        if not result.temp_token:
            raise HTTPException(status_code=500, detail="Login failed")
        return TwoFactorChallengeResponse(
            requires_2fa=True,
            temp_token=result.temp_token,
        )
    if result.access is None or result.refresh is None:
        raise HTTPException(status_code=500, detail="Login failed")
    _set_auth_cookies(response, result.access, result.refresh)
    return AuthResponse(
        user=UserRead.model_validate(result.user),
        access_token=result.access,
        vault_id=result.user.default_vault_id,
    )


@router.post("/forgot-password")
async def forgot_password(body: ForgotPasswordRequest, db: Db) -> dict[str, bool]:
    user = (
        await db.execute(select(User).where(User.email == body.email))
    ).scalar_one_or_none()
    if user:
        token = create_reset_token(str(user.id))
        settings = get_settings()
        reset_link = f"{settings.frontend_url}/auth/reset-password?token={token}"
        html = (
            "<p>You requested a password reset for your CLARA account.</p>"
            f'<p><a href="{reset_link}">Reset your password</a></p>'
            "<p>If you did not request this, ignore this email.</p>"
        )
        try:
            from clara.email.sender import get_sender

            get_sender().send(user.email, "CLARA — Password Reset", html)
        except Exception:
            logger.exception("Failed to send password reset email")
        logger.info("Password reset requested", extra={"user_id": str(user.id)})
    return {"ok": True}


@router.post("/reset-password")
async def reset_password(body: ResetPasswordRequest, db: Db) -> dict[str, bool]:
    payload = decode_reset_token(body.token)
    if payload is None:
        raise HTTPException(
            status_code=400, detail="Invalid or expired reset token"
        )
    user = await db.get(User, uuid.UUID(payload["sub"]))
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    user.hashed_password = hash_password(body.password)
    await db.flush()
    return {"ok": True}


@router.post("/refresh", response_model=AuthResponse)
async def refresh(request: Request, db: Db, response: Response) -> AuthResponse:
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="No refresh token")
    payload = decode_refresh_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    user = await db.get(User, uuid.UUID(payload["sub"]))
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    access = create_access_token(str(user.id))
    new_refresh = create_refresh_token(str(user.id))
    _set_auth_cookies(response, access, new_refresh)
    return AuthResponse(
        user=UserRead.model_validate(user),
        access_token=access,
        vault_id=user.default_vault_id,
    )


@router.post("/logout")
async def logout(request: Request, response: Response) -> dict[str, bool]:
    access_token = request.cookies.get("access_token")
    if access_token:
        payload = decode_access_token(access_token)
        if payload and payload.get("jti"):
            exp = payload.get("exp", 0)
            ttl = int(exp - datetime.now(UTC).timestamp())
            await blacklist_token(payload["jti"], ttl)
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"ok": True}


@router.get("/me", response_model=UserRead)
async def me(user: CurrentUser) -> UserRead:
    return UserRead.model_validate(user)


def _generate_recovery_codes(count: int = 8) -> list[str]:
    alphabet = string.ascii_uppercase + string.digits
    return [
        "".join(secrets.choice(alphabet) for _ in range(8))
        for _ in range(count)
    ]


def _build_qr_data_url(provisioning_uri: str) -> str:
    image = qrcode.make(provisioning_uri)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{encoded}"


@router.post("/2fa/setup", response_model=TwoFactorSetupResponse)
async def two_factor_setup(user: CurrentUser, db: Db) -> TwoFactorSetupResponse:
    existing_confirmed = (
        await db.execute(
            select(TotpDevice).where(
                TotpDevice.user_id == user.id,
                TotpDevice.confirmed.is_(True),
            )
        )
    ).scalar_one_or_none()
    if existing_confirmed:
        raise HTTPException(status_code=400, detail="2FA already enabled")

    await db.execute(
        delete(RecoveryCode).where(RecoveryCode.user_id == user.id)
    )
    await db.execute(
        delete(TotpDevice).where(
            TotpDevice.user_id == user.id,
            TotpDevice.confirmed.is_(False),
        )
    )

    secret = pyotp.random_base32()
    encrypted_secret = encrypt_totp_secret(secret)
    device = TotpDevice(
        user_id=user.id,
        secret=encrypted_secret,
        confirmed=False,
    )
    db.add(device)

    provisioning_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        user.email,
        issuer_name="CLARA",
    )

    recovery_codes = _generate_recovery_codes()
    for code in recovery_codes:
        db.add(
            RecoveryCode(
                user_id=user.id,
                code_hash=hash_password(code),
                used=False,
            )
        )

    await db.flush()
    return TwoFactorSetupResponse(
        provisioning_uri=provisioning_uri,
        qr_data_url=_build_qr_data_url(provisioning_uri),
        recovery_codes=recovery_codes,
    )


@router.post("/2fa/confirm")
async def two_factor_confirm(
    body: TwoFactorConfirmRequest, user: CurrentUser, db: Db
) -> dict[str, bool]:
    device = (
        await db.execute(
            select(TotpDevice).where(
                TotpDevice.user_id == user.id,
                TotpDevice.confirmed.is_(False),
            )
        )
    ).scalar_one_or_none()
    if device is None:
        raise HTTPException(status_code=400, detail="No pending 2FA setup")

    secret = decrypt_totp_secret(device.secret)
    if not pyotp.TOTP(secret).verify(body.code):
        raise HTTPException(status_code=400, detail="Invalid verification code")

    device.confirmed = True
    await db.flush()
    return {"ok": True}


@router.post("/2fa/verify", response_model=AuthResponse)
async def two_factor_verify(
    body: TwoFactorVerifyRequest, db: Db, response: Response
) -> AuthResponse:
    payload = decode_2fa_temp_token(body.temp_token)
    if payload is None:
        raise HTTPException(
            status_code=400, detail="Invalid or expired 2FA token"
        )

    user = await db.get(User, uuid.UUID(payload["sub"]))
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    device = (
        await db.execute(
            select(TotpDevice).where(
                TotpDevice.user_id == user.id,
                TotpDevice.confirmed.is_(True),
            )
        )
    ).scalar_one_or_none()
    if device is None:
        raise HTTPException(status_code=400, detail="2FA not configured")

    secret = decrypt_totp_secret(device.secret)
    if not pyotp.TOTP(secret).verify(body.code):
        raise HTTPException(status_code=400, detail="Invalid verification code")

    access = create_access_token(str(user.id))
    refresh = create_refresh_token(str(user.id))
    _set_auth_cookies(response, access, refresh)
    return AuthResponse(
        user=UserRead.model_validate(user),
        access_token=access,
        vault_id=user.default_vault_id,
    )


@router.post("/2fa/recovery", response_model=AuthResponse)
async def two_factor_recovery(
    body: TwoFactorVerifyRequest, db: Db, response: Response
) -> AuthResponse:
    payload = decode_2fa_temp_token(body.temp_token)
    if payload is None:
        raise HTTPException(
            status_code=400, detail="Invalid or expired 2FA token"
        )

    user = await db.get(User, uuid.UUID(payload["sub"]))
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    codes = (
        await db.execute(
            select(RecoveryCode).where(
                RecoveryCode.user_id == user.id,
                RecoveryCode.used.is_(False),
            )
        )
    ).scalars().all()
    matched = None
    for code in codes:
        if verify_password(body.code, code.code_hash):
            matched = code
            break

    if matched is None:
        raise HTTPException(status_code=400, detail="Invalid recovery code")

    matched.used = True
    await db.flush()

    access = create_access_token(str(user.id))
    refresh = create_refresh_token(str(user.id))
    _set_auth_cookies(response, access, refresh)
    return AuthResponse(
        user=UserRead.model_validate(user),
        access_token=access,
        vault_id=user.default_vault_id,
    )


@router.delete("/2fa")
async def two_factor_disable(user: CurrentUser, db: Db) -> dict[str, bool]:
    await db.execute(
        delete(TotpDevice).where(TotpDevice.user_id == user.id)
    )
    await db.execute(
        delete(RecoveryCode).where(RecoveryCode.user_id == user.id)
    )
    await db.flush()
    return {"ok": True}


# --- Personal Access Tokens ---


@router.get("/tokens", response_model=list[PatRead])
async def list_tokens(user: CurrentUser, db: Db) -> list[PatRead]:
    stmt = select(PersonalAccessToken).where(
        PersonalAccessToken.user_id == user.id
    )
    result = await db.execute(stmt)
    pats = result.scalars().all()
    return [
        PatRead(
            id=p.id,
            name=p.name,
            token_prefix=p.token_prefix,
            scopes=p.scopes,
            expires_at=p.expires_at,
            last_used_at=p.last_used_at,
            created_at=p.created_at,
        )
        for p in pats
    ]


@router.post("/tokens", response_model=PatCreateResponse, status_code=201)
async def create_token(body: PatCreate, user: CurrentUser, db: Db) -> PatCreateResponse:
    from datetime import UTC, datetime, timedelta

    raw_token = "pat_" + secrets.token_urlsafe(32)
    expires_at = None
    if body.expires_in_days:
        expires_at = datetime.now(UTC) + timedelta(days=body.expires_in_days)

    pat = PersonalAccessToken(
        user_id=user.id,
        name=body.name,
        token_prefix=raw_token[:12],
        token_hash=hash_password(raw_token),
        scopes=body.scopes,
        expires_at=expires_at,
    )
    db.add(pat)
    await db.flush()

    return PatCreateResponse(
        id=pat.id,
        name=pat.name,
        token_prefix=pat.token_prefix,
        scopes=body.scopes,
        expires_at=pat.expires_at,
        last_used_at=None,
        created_at=pat.created_at,
        token=raw_token,
    )


@router.delete("/tokens/{token_id}", status_code=204)
async def revoke_token(token_id: uuid.UUID, user: CurrentUser, db: Db) -> None:
    pat = await db.get(PersonalAccessToken, token_id)
    if pat is None or pat.user_id != user.id:
        raise HTTPException(status_code=404, detail="Token not found")
    await db.delete(pat)
    await db.flush()
