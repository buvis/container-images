import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DavSyncAccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    vault_id: uuid.UUID
    name: str
    server_url: str
    username: str
    carddav_enabled: bool
    caldav_enabled: bool
    carddav_path: str | None
    caldav_path: str | None
    sync_interval_minutes: int
    last_synced_at: datetime | None
    last_sync_status: str | None
    last_sync_error: str | None
    created_at: datetime
    updated_at: datetime


class DavSyncAccountCreate(BaseModel):
    name: str
    server_url: str
    username: str
    password: str  # plaintext, encrypted by service
    carddav_enabled: bool = True
    caldav_enabled: bool = True
    carddav_path: str | None = None
    caldav_path: str | None = None
    sync_interval_minutes: int = Field(default=15, ge=1)


class DavSyncAccountUpdate(BaseModel):
    name: str | None = None
    server_url: str | None = None
    username: str | None = None
    password: str | None = None
    carddav_enabled: bool | None = None
    caldav_enabled: bool | None = None
    carddav_path: str | None = None
    caldav_path: str | None = None
    sync_interval_minutes: int | None = Field(default=None, ge=1)


class DavSyncMappingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    account_id: uuid.UUID
    entity_type: str
    local_id: uuid.UUID
    remote_uid: str
    remote_etag: str | None
    local_updated_at: datetime
    remote_updated_at: datetime | None


class DavSyncStatusRead(BaseModel):
    last_synced_at: datetime | None
    last_sync_status: str | None
    last_sync_error: str | None
    mapping_counts: dict[str, int]  # entity_type -> count
