"""add sync tables

Revision ID: a1b2c3d4e5f6
Revises: c221f062fcc9
Create Date: 2026-02-18 22:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "c221f062fcc9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Activity: add duration_minutes
    op.add_column(
        "activities",
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
    )

    # DavSyncAccount
    op.create_table(
        "dav_sync_accounts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("vault_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("server_url", sa.String(2000), nullable=False),
        sa.Column("username", sa.String(255), nullable=False),
        sa.Column("encrypted_password", sa.Text(), nullable=False),
        sa.Column("carddav_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("caldav_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("carddav_path", sa.String(2000), nullable=True),
        sa.Column("caldav_path", sa.String(2000), nullable=True),
        sa.Column("sync_interval_minutes", sa.Integer(), nullable=False, server_default="15"),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_sync_status", sa.String(20), nullable=True),
        sa.Column("last_sync_error", sa.Text(), nullable=True),
        sa.Column("sync_token_card", sa.String(500), nullable=True),
        sa.Column("sync_token_cal", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["vault_id"], ["vaults.id"], name=op.f("fk_dav_sync_accounts_vault_id_vaults")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_dav_sync_accounts")),
    )
    op.create_index(op.f("ix_dav_sync_accounts_vault_id"), "dav_sync_accounts", ["vault_id"])

    # DavSyncMapping
    op.create_table(
        "dav_sync_mappings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("vault_id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("entity_type", sa.String(20), nullable=False),
        sa.Column("local_id", sa.Uuid(), nullable=False),
        sa.Column("remote_uid", sa.String(500), nullable=False),
        sa.Column("remote_etag", sa.String(500), nullable=True),
        sa.Column("remote_href", sa.String(2000), nullable=True),
        sa.Column("local_updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("remote_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["vault_id"], ["vaults.id"], name=op.f("fk_dav_sync_mappings_vault_id_vaults")),
        sa.ForeignKeyConstraint(["account_id"], ["dav_sync_accounts.id"], name=op.f("fk_dav_sync_mappings_account_id_dav_sync_accounts")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_dav_sync_mappings")),
        sa.UniqueConstraint("account_id", "entity_type", "local_id", name="uq_dav_mapping_local"),
        sa.UniqueConstraint("account_id", "entity_type", "remote_uid", name="uq_dav_mapping_remote"),
    )
    op.create_index(op.f("ix_dav_sync_mappings_vault_id"), "dav_sync_mappings", ["vault_id"])

    # GitSyncConfig
    op.create_table(
        "git_sync_configs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("vault_id", sa.Uuid(), nullable=False),
        sa.Column("repo_url", sa.String(2000), nullable=False),
        sa.Column("branch", sa.String(255), nullable=False, server_default="main"),
        sa.Column("auth_type", sa.String(20), nullable=False),
        sa.Column("credential_encrypted", sa.Text(), nullable=False),
        sa.Column("subfolder", sa.String(500), nullable=False, server_default=""),
        sa.Column("sync_interval_minutes", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("field_mapping_json", sa.Text(), nullable=True),
        sa.Column("section_mapping_json", sa.Text(), nullable=True),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_sync_status", sa.String(20), nullable=True),
        sa.Column("last_sync_error", sa.Text(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["vault_id"], ["vaults.id"], name=op.f("fk_git_sync_configs_vault_id_vaults")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_git_sync_configs")),
        sa.UniqueConstraint("vault_id", name="uq_git_sync_configs_vault_id"),
    )
    op.create_index(op.f("ix_git_sync_configs_vault_id"), "git_sync_configs", ["vault_id"])

    # GitSyncMapping
    op.create_table(
        "git_sync_mappings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("vault_id", sa.Uuid(), nullable=False),
        sa.Column("config_id", sa.Uuid(), nullable=False),
        sa.Column("contact_id", sa.Uuid(), nullable=False),
        sa.Column("markdown_id", sa.String(14), nullable=False),
        sa.Column("file_path", sa.String(1000), nullable=False),
        sa.Column("last_db_updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_file_updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("file_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["vault_id"], ["vaults.id"], name=op.f("fk_git_sync_mappings_vault_id_vaults")),
        sa.ForeignKeyConstraint(["config_id"], ["git_sync_configs.id"], name=op.f("fk_git_sync_mappings_config_id_git_sync_configs")),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"], name=op.f("fk_git_sync_mappings_contact_id_contacts")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_git_sync_mappings")),
        sa.UniqueConstraint("config_id", "contact_id", name="uq_git_mapping_contact"),
        sa.UniqueConstraint("config_id", "markdown_id", name="uq_git_mapping_markdown"),
    )
    op.create_index(op.f("ix_git_sync_mappings_vault_id"), "git_sync_mappings", ["vault_id"])


def downgrade() -> None:
    op.drop_table("git_sync_mappings")
    op.drop_table("git_sync_configs")
    op.drop_table("dav_sync_mappings")
    op.drop_table("dav_sync_accounts")
    op.drop_column("activities", "duration_minutes")
