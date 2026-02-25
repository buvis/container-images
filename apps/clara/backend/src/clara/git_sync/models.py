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


class GitSyncConfig(VaultScopedModel):
    __tablename__ = "git_sync_configs"
    __table_args__ = (
        UniqueConstraint("vault_id", name="uq_git_sync_configs_vault_id"),
    )

    repo_url: Mapped[str] = mapped_column(String(2000))
    branch: Mapped[str] = mapped_column(String(255), default="main")
    auth_type: Mapped[str] = mapped_column(String(20))  # ssh_key / pat
    credential_encrypted: Mapped[str] = mapped_column(Text)
    subfolder: Mapped[str] = mapped_column(String(500), default="")
    sync_interval_minutes: Mapped[int] = mapped_column(Integer, default=60)
    field_mapping_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    section_mapping_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_sync_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    last_sync_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    mappings: Mapped[list["GitSyncMapping"]] = relationship(
        back_populates="config", cascade="all, delete-orphan"
    )


class GitSyncMapping(VaultScopedModel):
    __tablename__ = "git_sync_mappings"
    __table_args__ = (
        UniqueConstraint("config_id", "contact_id", name="uq_git_mapping_contact"),
        UniqueConstraint("config_id", "markdown_id", name="uq_git_mapping_markdown"),
    )

    config_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("git_sync_configs.id")
    )
    contact_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("contacts.id"))
    markdown_id: Mapped[str] = mapped_column(String(14))
    file_path: Mapped[str] = mapped_column(String(1000))
    last_db_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_file_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    file_hash: Mapped[str] = mapped_column(String(64))

    config: Mapped[GitSyncConfig] = relationship(back_populates="mappings")
