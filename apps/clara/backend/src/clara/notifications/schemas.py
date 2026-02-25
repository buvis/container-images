import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    user_id: uuid.UUID
    vault_id: uuid.UUID
    title: str
    body: str
    link: str | None
    read: bool
    created_at: datetime


class NotificationMarkRead(BaseModel):
    read: bool = True


class UnreadCount(BaseModel):
    count: int
