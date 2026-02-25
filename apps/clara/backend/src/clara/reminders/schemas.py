import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

# --- Reminder schemas ---


class ReminderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    vault_id: uuid.UUID
    contact_id: uuid.UUID | None
    title: str
    description: str | None
    next_expected_date: date
    frequency_type: str
    frequency_number: int
    last_triggered_at: datetime | None
    status: str
    created_at: datetime
    updated_at: datetime


class ReminderCreate(BaseModel):
    contact_id: uuid.UUID | None = None
    title: str
    description: str | None = None
    next_expected_date: date
    frequency_type: Literal["one_time", "week", "month", "year"] = "one_time"
    frequency_number: int = 1


class ReminderUpdate(BaseModel):
    contact_id: uuid.UUID | None = None
    title: str | None = None
    description: str | None = None
    next_expected_date: date | None = None
    frequency_type: Literal["one_time", "week", "month", "year"] | None = None
    frequency_number: int | None = None
    status: str | None = None


# --- StayInTouchConfig schemas ---


class StayInTouchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    vault_id: uuid.UUID
    contact_id: uuid.UUID
    target_interval_days: int
    last_contacted_at: datetime | None
    created_at: datetime
    updated_at: datetime


class StayInTouchCreateOrUpdate(BaseModel):
    target_interval_days: int
    last_contacted_at: datetime | None = None
