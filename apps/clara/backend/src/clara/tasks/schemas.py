import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    vault_id: uuid.UUID
    title: str
    description: str | None
    due_date: date | None
    status: str
    priority: int
    contact_id: uuid.UUID | None
    activity_id: uuid.UUID | None
    created_by_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    due_date: date | None = None
    status: Literal["pending", "in_progress", "done"] = "pending"
    priority: int = Field(default=0, ge=0, le=3)
    contact_id: uuid.UUID | None = None
    activity_id: uuid.UUID | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    due_date: date | None = None
    status: Literal["pending", "in_progress", "done"] | None = None
    priority: int | None = Field(default=None, ge=0, le=3)
    contact_id: uuid.UUID | None = None
    activity_id: uuid.UUID | None = None
