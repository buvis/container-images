import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from clara.base.model import VaultScopedModel


class JournalEntry(VaultScopedModel):
    __tablename__ = "journal_entries"
    entry_date: Mapped[date] = mapped_column(Date)
    title: Mapped[str] = mapped_column(String(500), default="")
    body_markdown: Mapped[str] = mapped_column(Text, default="")
    mood: Mapped[int | None] = mapped_column(Integer)
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id")
    )
    contacts: Mapped[list["JournalEntryContact"]] = relationship(
        cascade="all, delete-orphan"
    )


class JournalEntryContact(VaultScopedModel):
    __tablename__ = "journal_entry_contacts"
    journal_entry_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("journal_entries.id")
    )
    contact_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("contacts.id")
    )
