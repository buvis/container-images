import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from clara.base.model import Base, SoftDeleteMixin, TimestampMixin


class Vault(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "vaults"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=True
    )
    owner: Mapped["User"] = relationship(foreign_keys=[owner_user_id])
    members: Mapped[list["VaultMembership"]] = relationship(back_populates="vault")


class User(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), default="")
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    locale: Mapped[str] = mapped_column(String(10), default="en")
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    default_vault_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("vaults.id"), nullable=True
    )
    memberships: Mapped[list["VaultMembership"]] = relationship(back_populates="user")


class VaultMembership(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "vault_memberships"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"))
    vault_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("vaults.id"))
    role: Mapped[str] = mapped_column(String(50), default="owner")

    user: Mapped[User] = relationship(back_populates="memberships")
    vault: Mapped[Vault] = relationship(back_populates="members")


class TotpDevice(TimestampMixin, Base):
    __tablename__ = "totp_devices"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"))
    secret: Mapped[str] = mapped_column(String(255))
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)


class RecoveryCode(TimestampMixin, Base):
    __tablename__ = "recovery_codes"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"))
    code_hash: Mapped[str] = mapped_column(String(255))
    used: Mapped[bool] = mapped_column(Boolean, default=False)


class PersonalAccessToken(TimestampMixin, Base):
    __tablename__ = "personal_access_tokens"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(255))
    token_prefix: Mapped[str] = mapped_column(String(12))
    token_hash: Mapped[str] = mapped_column(Text)
    scopes: Mapped[list[str]] = mapped_column(
        JSON, default=list, server_default='["read","write"]'
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class VaultSettings(TimestampMixin, Base):
    __tablename__ = "vault_settings"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    vault_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("vaults.id"), unique=True
    )
    language: Mapped[str] = mapped_column(String(10), default="en")
    date_format: Mapped[str] = mapped_column(String(20), default="YYYY-MM-DD")
    time_format: Mapped[str] = mapped_column(String(5), default="24h")
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    feature_flags: Mapped[dict[str, bool]] = mapped_column(
        JSON,
        default=dict,
        server_default='{"debts":true,"gifts":true,"pets":true,"journal":true}',
    )
