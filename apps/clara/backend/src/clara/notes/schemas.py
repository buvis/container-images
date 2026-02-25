import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NoteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    vault_id: uuid.UUID
    contact_id: uuid.UUID | None
    activity_id: uuid.UUID | None
    title: str
    body_markdown: str
    created_by_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class NoteCreate(BaseModel):
    contact_id: uuid.UUID | None = None
    activity_id: uuid.UUID | None = None
    title: str = ""
    body_markdown: str = ""


class NoteUpdate(BaseModel):
    contact_id: uuid.UUID | None = None
    activity_id: uuid.UUID | None = None
    title: str | None = None
    body_markdown: str | None = None
