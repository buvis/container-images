import uuid

from sqlalchemy import ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from clara.base.model import VaultScopedModel


class Note(VaultScopedModel):
    __tablename__ = "notes"
    contact_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("contacts.id"), nullable=True
    )
    activity_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("activities.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(500), default="")
    body_markdown: Mapped[str] = mapped_column(Text, default="")
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id")
    )
