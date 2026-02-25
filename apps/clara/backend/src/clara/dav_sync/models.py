import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from clara.base.model import VaultScopedModel


class DavSyncAccount(VaultScopedModel):
    __tablename__ = "dav_sync_accounts"

    name: Mapped[str] = mapped_column(String(255))
    server_url: Mapped[str] = mapped_column(String(2000))
    username: Mapped[str] = mapped_column(String(255))
    encrypted_password: Mapped[str] = mapped_column(Text)
    carddav_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    caldav_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    carddav_path: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    caldav_path: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    sync_interval_minutes: Mapped[int] = mapped_column(Integer, default=15)
    last_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_sync_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    last_sync_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    sync_token_card: Mapped[str | None] = mapped_column(String(500), nullable=True)
    sync_token_cal: Mapped[str | None] = mapped_column(String(500), nullable=True)

    mappings: Mapped[list["DavSyncMapping"]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )


class DavSyncMapping(VaultScopedModel):
    __tablename__ = "dav_sync_mappings"
    __table_args__ = (
        UniqueConstraint(
            "account_id", "entity_type", "local_id", name="uq_dav_mapping_local"
        ),
        UniqueConstraint(
            "account_id", "entity_type", "remote_uid", name="uq_dav_mapping_remote"
        ),
    )

    account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("dav_sync_accounts.id")
    )
    entity_type: Mapped[str] = mapped_column(String(20))
    local_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    remote_uid: Mapped[str] = mapped_column(String(500))
    remote_etag: Mapped[str | None] = mapped_column(String(500), nullable=True)
    remote_href: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    local_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    remote_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    account: Mapped[DavSyncAccount] = relationship(back_populates="mappings")
