import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

# --- ActivityType schemas ---


class ActivityTypeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    vault_id: uuid.UUID
    name: str
    icon: str
    color: str
    created_at: datetime
    updated_at: datetime


class ActivityTypeCreate(BaseModel):
    name: str
    icon: str = ""
    color: str = "#6b7280"


class ActivityTypeUpdate(BaseModel):
    name: str | None = None
    icon: str | None = None
    color: str | None = None


# --- ActivityParticipant schemas ---


class ParticipantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    contact_id: uuid.UUID
    role: str


class ParticipantInput(BaseModel):
    contact_id: uuid.UUID
    role: str = ""


# --- Activity schemas ---


class ActivityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    vault_id: uuid.UUID
    activity_type_id: uuid.UUID | None
    title: str
    description: str | None
    happened_at: datetime
    location: str | None
    participants: list[ParticipantRead]
    created_at: datetime
    updated_at: datetime


class ActivityCreate(BaseModel):
    activity_type_id: uuid.UUID | None = None
    title: str
    description: str | None = None
    happened_at: datetime
    location: str | None = None
    participants: list[ParticipantInput] = []


class ActivityUpdate(BaseModel):
    activity_type_id: uuid.UUID | None = None
    title: str | None = None
    description: str | None = None
    happened_at: datetime | None = None
    location: str | None = None
    participants: list[ParticipantInput] | None = None
