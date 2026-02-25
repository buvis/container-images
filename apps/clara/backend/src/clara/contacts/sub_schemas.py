"""Pydantic schemas for contact sub-resources and relationship types."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class ContactMethodRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    vault_id: uuid.UUID
    contact_id: uuid.UUID
    type: str
    label: str
    value: str
    created_at: datetime
    updated_at: datetime


class ContactMethodCreate(BaseModel):
    type: str
    label: str = ""
    value: str


class ContactMethodUpdate(BaseModel):
    type: str | None = None
    label: str | None = None
    value: str | None = None


class AddressRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    vault_id: uuid.UUID
    contact_id: uuid.UUID
    label: str
    line1: str
    line2: str | None
    city: str
    postal_code: str
    country: str
    geo_location: str | None
    created_at: datetime
    updated_at: datetime


class AddressCreate(BaseModel):
    label: str = ""
    line1: str = ""
    line2: str | None = None
    city: str = ""
    postal_code: str = ""
    country: str = ""
    geo_location: str | None = None


class AddressUpdate(BaseModel):
    label: str | None = None
    line1: str | None = None
    line2: str | None = None
    city: str | None = None
    postal_code: str | None = None
    country: str | None = None
    geo_location: str | None = None


class ContactRelationshipRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    vault_id: uuid.UUID
    contact_id: uuid.UUID
    other_contact_id: uuid.UUID
    relationship_type_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class ContactRelationshipCreate(BaseModel):
    other_contact_id: uuid.UUID
    relationship_type_id: uuid.UUID


class PetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    vault_id: uuid.UUID
    contact_id: uuid.UUID
    name: str
    species: str
    birthdate: date | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class PetCreate(BaseModel):
    name: str
    species: str = ""
    birthdate: date | None = None
    notes: str | None = None


class PetUpdate(BaseModel):
    name: str | None = None
    species: str | None = None
    birthdate: date | None = None
    notes: str | None = None


class TagRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    vault_id: uuid.UUID
    name: str
    color: str
    created_at: datetime
    updated_at: datetime


class TagCreate(BaseModel):
    name: str
    color: str = "#6b7280"


class ContactTagAttach(BaseModel):
    tag_id: uuid.UUID


class RelationshipTypeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    vault_id: uuid.UUID
    name: str
    inverse_type_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class RelationshipTypeCreate(BaseModel):
    name: str
    inverse_type_id: uuid.UUID | None = None


class RelationshipTypeUpdate(BaseModel):
    name: str | None = None
    inverse_type_id: uuid.UUID | None = None
