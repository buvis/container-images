import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict

GiftDirection = Literal["given", "received", "idea"]


class GiftRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    vault_id: uuid.UUID
    contact_id: uuid.UUID
    direction: GiftDirection
    name: str
    description: str | None
    amount: Decimal | None
    currency: str
    status: str
    link: str | None
    created_at: datetime
    updated_at: datetime


class GiftCreate(BaseModel):
    contact_id: uuid.UUID
    direction: GiftDirection
    name: str
    description: str | None = None
    amount: Decimal | None = None
    currency: str = "USD"
    status: str = "idea"
    link: str | None = None


class GiftUpdate(BaseModel):
    contact_id: uuid.UUID | None = None
    direction: GiftDirection | None = None
    name: str | None = None
    description: str | None = None
    amount: Decimal | None = None
    currency: str | None = None
    status: str | None = None
    link: str | None = None
