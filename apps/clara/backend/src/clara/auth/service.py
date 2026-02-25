from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from clara.auth.models import TotpDevice, User, Vault, VaultMembership, VaultSettings
from clara.auth.schemas import LoginRequest, RegisterRequest
from clara.auth.security import (
    create_2fa_temp_token,
    create_access_token,
    create_refresh_token,
    hash_password,
    needs_rehash,
    verify_password,
)
from clara.exceptions import ConflictError, InvalidCredentialsError


@dataclass(frozen=True)
class LoginResult:
    user: User
    access: str | None
    refresh: str | None
    temp_token: str | None

    @property
    def requires_2fa(self) -> bool:
        return self.temp_token is not None


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def register(
        self, data: RegisterRequest
    ) -> tuple[User, Vault, str, str]:
        existing = (
            await self.session.execute(
                select(User).where(User.email == data.email)
            )
        ).scalar_one_or_none()
        if existing:
            raise ConflictError("Email already registered")

        vault = Vault(name=f"{data.name or data.email}'s vault")
        self.session.add(vault)
        await self.session.flush()

        user = User(
            email=data.email,
            name=data.name,
            hashed_password=hash_password(data.password),
            default_vault_id=vault.id,
        )
        self.session.add(user)
        await self.session.flush()

        vault.owner_user_id = user.id

        membership = VaultMembership(
            user_id=user.id, vault_id=vault.id, role="owner"
        )
        self.session.add(membership)
        self.session.add(VaultSettings(vault_id=vault.id))
        await self.session.flush()

        access = create_access_token(str(user.id))
        refresh = create_refresh_token(str(user.id))
        return user, vault, access, refresh

    async def login(self, data: LoginRequest) -> LoginResult:
        user = (
            await self.session.execute(
                select(User).where(User.email == data.email)
            )
        ).scalar_one_or_none()
        if user is None or not verify_password(
            data.password, user.hashed_password
        ):
            raise InvalidCredentialsError("Invalid credentials")

        # Upgrade legacy bcrypt hash to argon2
        if needs_rehash(user.hashed_password):
            user.hashed_password = hash_password(data.password)
            await self.session.flush()

        has_device = (
            await self.session.execute(
                select(TotpDevice).where(
                    TotpDevice.user_id == user.id,
                    TotpDevice.confirmed.is_(True),
                )
            )
        ).scalar_one_or_none()
        if has_device:
            temp_token = create_2fa_temp_token(str(user.id))
            return LoginResult(
                user=user,
                access=None,
                refresh=None,
                temp_token=temp_token,
            )

        access = create_access_token(str(user.id))
        refresh = create_refresh_token(str(user.id))
        return LoginResult(
            user=user,
            access=access,
            refresh=refresh,
            temp_token=None,
        )
