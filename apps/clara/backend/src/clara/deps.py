import uuid
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from clara.auth.models import PersonalAccessToken, User, VaultMembership
from clara.auth.security import decode_access_token, verify_password
from clara.database import get_session
from clara.redis import is_token_blacklisted

Db = Annotated[AsyncSession, Depends(get_session)]


async def _extract_token(request: Request) -> str:
    token = request.cookies.get("access_token")
    if token:
        return token
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.removeprefix("Bearer ")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
    )


async def _authenticate_pat(
    token: str, session: AsyncSession
) -> tuple[User, PersonalAccessToken] | None:
    """Look up user via Personal Access Token."""
    prefix = token[:12]
    stmt = select(PersonalAccessToken).where(
        PersonalAccessToken.token_prefix == prefix
    )
    pats = (await session.execute(stmt)).scalars().all()
    for pat in pats:
        if verify_password(token, pat.token_hash):
            if pat.expires_at and pat.expires_at < datetime.now(UTC):
                return None
            pat.last_used_at = datetime.now(UTC)
            await session.flush()
            user = await session.get(User, pat.user_id)
            return (user, pat) if user else None
    return None


_WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


async def get_current_user(
    request: Request,
    token: str = Depends(_extract_token),
    session: AsyncSession = Depends(get_session),
) -> User:
    # PAT auth
    if token.startswith("pat_"):
        result = await _authenticate_pat(token, session)
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )
        user, pat = result
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account deactivated",
            )
        scopes = pat.scopes
        if request.method in _WRITE_METHODS and "write" not in scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token scope insufficient",
            )
        if request.method not in _WRITE_METHODS and "read" not in scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token scope insufficient",
            )
        return user

    # JWT auth
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    jti = payload.get("jti")
    if jti and await is_token_blacklisted(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
        )
    jwt_user = await session.get(User, uuid.UUID(payload["sub"]))
    if jwt_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    if not jwt_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account deactivated",
        )
    return jwt_user


async def get_vault_membership(
    vault_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> VaultMembership:
    stmt = select(VaultMembership).where(
        VaultMembership.user_id == user.id,
        VaultMembership.vault_id == vault_id,
    )
    membership = (await session.execute(stmt)).scalar_one_or_none()
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No access to this vault",
        )
    return membership


CurrentUser = Annotated[User, Depends(get_current_user)]
VaultAccess = Annotated[VaultMembership, Depends(get_vault_membership)]


def require_role(*roles: str) -> Any:
    """Dependency factory: checks membership role against allowed roles."""

    async def _check(
        membership: VaultMembership = Depends(get_vault_membership),
    ) -> VaultMembership:
        if membership.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role: {', '.join(roles)}",
            )
        return membership

    return Depends(_check)
