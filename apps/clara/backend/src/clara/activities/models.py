import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from clara.base.model import VaultScopedModel


class ActivityType(VaultScopedModel):
    __tablename__ = "activity_types"
    name: Mapped[str] = mapped_column(String(100))
    icon: Mapped[str] = mapped_column(String(50), default="")
    color: Mapped[str] = mapped_column(String(7), default="#6b7280")


class Activity(VaultScopedModel):
    __tablename__ = "activities"
    activity_type_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("activity_types.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    happened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    location: Mapped[str | None] = mapped_column(String(500))
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    participants: Mapped[list["ActivityParticipant"]] = relationship(
        back_populates="activity", cascade="all, delete-orphan"
    )


class ActivityParticipant(VaultScopedModel):
    __tablename__ = "activity_participants"
    activity_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("activities.id")
    )
    contact_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("contacts.id")
    )
    role: Mapped[str] = mapped_column(String(100), default="")
    activity: Mapped[Activity] = relationship(back_populates="participants")
