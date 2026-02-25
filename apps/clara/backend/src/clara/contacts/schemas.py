import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from clara.contacts.sub_schemas import (
    AddressRead,
    ContactMethodRead,
    ContactRelationshipRead,
    PetRead,
    TagRead,
)


class ContactRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    vault_id: uuid.UUID
    first_name: str
    last_name: str
    nickname: str | None
    birthdate: date | None
    gender: str | None
    pronouns: str | None
    notes_summary: str | None
    favorite: bool
    photo_file_id: uuid.UUID | None
    template_id: uuid.UUID | None
    contact_methods: list[ContactMethodRead]
    addresses: list[AddressRead]
    tags: list[TagRead]
    pets: list[PetRead]
    relationships: list[ContactRelationshipRead]
    created_at: datetime
    updated_at: datetime


class ContactCreate(BaseModel):
    first_name: str
    last_name: str = ""
    nickname: str | None = None
    birthdate: date | None = None
    gender: str | None = None
    pronouns: str | None = None
    notes_summary: str | None = None
    favorite: bool = False


class ContactUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    nickname: str | None = None
    birthdate: date | None = None
    gender: str | None = None
    pronouns: str | None = None
    notes_summary: str | None = None
    favorite: bool | None = None
    photo_file_id: uuid.UUID | None = None
