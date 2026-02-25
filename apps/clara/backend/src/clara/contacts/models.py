import uuid
from datetime import date

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    ForeignKey,
    String,
    Table,
    Text,
    Uuid,
    func,
)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.expression import ColumnElement

from clara.base.model import Base, VaultScopedModel

contact_tags = Table(
    "contact_tags",
    Base.metadata,
    Column(
        "contact_id",
        Uuid,
        ForeignKey("contacts.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id",
        Uuid,
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Contact(VaultScopedModel):
    __tablename__ = "contacts"

    first_name: Mapped[str] = mapped_column(String(255))
    last_name: Mapped[str] = mapped_column(String(255), default="")
    nickname: Mapped[str | None] = mapped_column(String(255))
    birthdate: Mapped[date | None] = mapped_column(Date)
    gender: Mapped[str | None] = mapped_column(String(50))
    pronouns: Mapped[str | None] = mapped_column(String(100))
    notes_summary: Mapped[str | None] = mapped_column(Text)
    favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    photo_file_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    template_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("templates.id"), nullable=True
    )

    contact_methods: Mapped[list["ContactMethod"]] = relationship(
        back_populates="contact", cascade="all, delete-orphan"
    )
    addresses: Mapped[list["Address"]] = relationship(
        back_populates="contact", cascade="all, delete-orphan"
    )
    tags: Mapped[list["Tag"]] = relationship(
        secondary=contact_tags, back_populates="contacts"
    )
    pets: Mapped[list["Pet"]] = relationship(
        back_populates="contact", cascade="all, delete-orphan"
    )
    relationships: Mapped[list["ContactRelationship"]] = relationship(
        foreign_keys="ContactRelationship.contact_id",
        cascade="all, delete-orphan",
    )

    @hybrid_property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    @full_name.inplace.expression
    @classmethod
    def _full_name_expr(cls) -> ColumnElement[str]:
        return func.concat(cls.first_name, " ", cls.last_name)


class ContactMethod(VaultScopedModel):
    __tablename__ = "contact_methods"

    contact_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("contacts.id")
    )
    type: Mapped[str] = mapped_column(String(50))
    label: Mapped[str] = mapped_column(String(100), default="")
    value: Mapped[str] = mapped_column(String(500))

    contact: Mapped[Contact] = relationship(back_populates="contact_methods")


class Address(VaultScopedModel):
    __tablename__ = "addresses"

    contact_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("contacts.id")
    )
    label: Mapped[str] = mapped_column(String(100), default="")
    line1: Mapped[str] = mapped_column(String(500), default="")
    line2: Mapped[str | None] = mapped_column(String(500))
    city: Mapped[str] = mapped_column(String(255), default="")
    postal_code: Mapped[str] = mapped_column(String(50), default="")
    country: Mapped[str] = mapped_column(String(100), default="")
    geo_location: Mapped[str | None] = mapped_column(String(50), default=None)

    contact: Mapped[Contact] = relationship(back_populates="addresses")


class RelationshipType(VaultScopedModel):
    __tablename__ = "relationship_types"

    name: Mapped[str] = mapped_column(String(100))
    inverse_type_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("relationship_types.id"), nullable=True
    )
    inverse_type: Mapped["RelationshipType | None"] = relationship(
        remote_side="RelationshipType.id"
    )


class ContactRelationship(VaultScopedModel):
    __tablename__ = "contact_relationships"

    contact_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("contacts.id")
    )
    other_contact_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("contacts.id")
    )
    relationship_type_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("relationship_types.id")
    )

    contact: Mapped["Contact"] = relationship(
        foreign_keys=[contact_id], overlaps="relationships"
    )
    other_contact: Mapped["Contact"] = relationship(foreign_keys=[other_contact_id])
    relationship_type: Mapped["RelationshipType"] = relationship()


class Tag(VaultScopedModel):
    __tablename__ = "tags"

    name: Mapped[str] = mapped_column(String(100))
    color: Mapped[str] = mapped_column(String(7), default="#6b7280")

    contacts: Mapped[list[Contact]] = relationship(
        secondary=contact_tags, back_populates="tags"
    )


class Pet(VaultScopedModel):
    __tablename__ = "pets"

    contact_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("contacts.id")
    )
    name: Mapped[str] = mapped_column(String(255))
    species: Mapped[str] = mapped_column(String(100), default="")
    birthdate: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)

    contact: Mapped[Contact] = relationship(back_populates="pets")
