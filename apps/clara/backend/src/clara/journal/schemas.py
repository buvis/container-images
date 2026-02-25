import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class JournalEntryContactRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    journal_entry_id: uuid.UUID
    contact_id: uuid.UUID


class JournalEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    vault_id: uuid.UUID
    entry_date: date
    title: str
    body_markdown: str
    mood: int | None
    created_by_id: uuid.UUID
    contacts: list[JournalEntryContactRead]
    created_at: datetime
    updated_at: datetime


class JournalEntryCreate(BaseModel):
    entry_date: date
    title: str = ""
    body_markdown: str = ""
    mood: int | None = Field(None, ge=1, le=5)
    contact_ids: list[uuid.UUID] = []


class JournalEntryUpdate(BaseModel):
    entry_date: date | None = None
    title: str | None = None
    body_markdown: str | None = None
    mood: int | None = Field(None, ge=1, le=5)
    contact_ids: list[uuid.UUID] | None = None
