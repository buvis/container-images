import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class GitSyncConfigRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    vault_id: uuid.UUID
    repo_url: str
    branch: str
    auth_type: str
    subfolder: str
    sync_interval_minutes: int
    field_mapping_json: str | None
    section_mapping_json: str | None
    last_sync_at: datetime | None
    last_sync_status: str | None
    last_sync_error: str | None
    enabled: bool
    created_at: datetime
    updated_at: datetime


class GitSyncConfigCreate(BaseModel):
    repo_url: str
    branch: str = "main"
    auth_type: Literal["ssh_key", "pat"]
    credential: str  # plaintext, encrypted by service
    subfolder: str = ""
    sync_interval_minutes: int = Field(default=60, ge=1)
    field_mapping_json: str | None = None
    section_mapping_json: str | None = None
    enabled: bool = True


class GitSyncConfigUpdate(BaseModel):
    repo_url: str | None = None
    branch: str | None = None
    auth_type: Literal["ssh_key", "pat"] | None = None
    credential: str | None = None
    subfolder: str | None = None
    sync_interval_minutes: int | None = Field(default=None, ge=1)
    field_mapping_json: str | None = None
    section_mapping_json: str | None = None
    enabled: bool | None = None


class GitSyncMappingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    config_id: uuid.UUID
    contact_id: uuid.UUID
    markdown_id: str
    file_path: str
    last_db_updated_at: datetime
    last_file_updated_at: datetime
    file_hash: str


class GitSyncStatusRead(BaseModel):
    last_sync_at: datetime | None
    last_sync_status: str | None
    last_sync_error: str | None
    mapping_count: int
