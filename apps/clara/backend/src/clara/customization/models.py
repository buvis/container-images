import uuid

from sqlalchemy import ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from clara.base.model import VaultScopedModel


class Template(VaultScopedModel):
    __tablename__ = "templates"
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    pages: Mapped[list["TemplatePage"]] = relationship(
        back_populates="template", cascade="all, delete-orphan"
    )


class TemplatePage(VaultScopedModel):
    __tablename__ = "template_pages"
    template_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("templates.id")
    )
    slug: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(255))
    order: Mapped[int] = mapped_column(Integer, default=0)
    template: Mapped[Template] = relationship(back_populates="pages")
    modules: Mapped[list["TemplateModule"]] = relationship(
        back_populates="page", cascade="all, delete-orphan"
    )


class TemplateModule(VaultScopedModel):
    __tablename__ = "template_modules"
    page_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("template_pages.id")
    )
    module_type: Mapped[str] = mapped_column(String(100))
    order: Mapped[int] = mapped_column(Integer, default=0)
    config_json: Mapped[str | None] = mapped_column(Text)
    page: Mapped[TemplatePage] = relationship(back_populates="modules")


class CustomFieldDefinition(VaultScopedModel):
    __tablename__ = "custom_field_definitions"
    scope: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(255))
    data_type: Mapped[str] = mapped_column(String(50))
    config_json: Mapped[str | None] = mapped_column(Text)


class CustomFieldValue(VaultScopedModel):
    __tablename__ = "custom_field_values"
    definition_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("custom_field_definitions.id")
    )
    entity_type: Mapped[str] = mapped_column(String(50))
    entity_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    value_json: Mapped[str] = mapped_column(Text, default="")
