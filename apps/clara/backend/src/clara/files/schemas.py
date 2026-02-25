import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    vault_id: uuid.UUID
    uploader_id: uuid.UUID
    filename: str
    mime_type: str
    size_bytes: int
    created_at: datetime
    updated_at: datetime


class FileLinkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    vault_id: uuid.UUID
    file_id: uuid.UUID
    target_type: str
    target_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class FileUpdate(BaseModel):
    filename: str | None = None


class FileLinkCreate(BaseModel):
    file_id: uuid.UUID
    target_type: str
    target_id: uuid.UUID
