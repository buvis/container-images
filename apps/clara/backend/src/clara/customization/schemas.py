import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

# --- Template Module ---


class TemplateModuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    page_id: uuid.UUID
    module_type: str
    order: int
    config_json: str | None
    created_at: datetime
    updated_at: datetime


class TemplateModuleCreate(BaseModel):
    module_type: str
    order: int = 0
    config_json: str | None = None


class TemplateModuleUpdate(BaseModel):
    module_type: str | None = None
    order: int | None = None
    config_json: str | None = None


# --- Template Page ---


class TemplatePageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    template_id: uuid.UUID
    slug: str
    name: str
    order: int
    modules: list[TemplateModuleRead]
    created_at: datetime
    updated_at: datetime


class TemplatePageCreate(BaseModel):
    slug: str
    name: str
    order: int = 0
    modules: list[TemplateModuleCreate] = []


class TemplatePageUpdate(BaseModel):
    slug: str | None = None
    name: str | None = None
    order: int | None = None


# --- Template ---


class TemplateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    vault_id: uuid.UUID
    name: str
    description: str | None
    pages: list[TemplatePageRead]
    created_at: datetime
    updated_at: datetime


class TemplateCreate(BaseModel):
    name: str
    description: str | None = None
    pages: list[TemplatePageCreate] = []


class TemplateUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


# --- Custom Field Definition ---


class CustomFieldDefinitionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    vault_id: uuid.UUID
    scope: str
    name: str
    slug: str
    data_type: str
    config_json: str | None
    created_at: datetime
    updated_at: datetime


class CustomFieldDefinitionCreate(BaseModel):
    scope: Literal["contact", "activity", "task"]
    name: str
    slug: str
    data_type: Literal["text", "number", "date", "boolean", "select"]
    config_json: str | None = None


class CustomFieldDefinitionUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    data_type: Literal["text", "number", "date", "boolean", "select"] | None = None
    config_json: str | None = None


# --- Custom Field Value ---


class CustomFieldValueRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    vault_id: uuid.UUID
    definition_id: uuid.UUID
    entity_type: str
    entity_id: uuid.UUID
    value_json: str
    created_at: datetime
    updated_at: datetime


class CustomFieldValueSet(BaseModel):
    definition_id: uuid.UUID
    entity_type: str
    entity_id: uuid.UUID
    value_json: str
