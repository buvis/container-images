import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from clara.base.model import VaultScopedModel


class Reminder(VaultScopedModel):
    __tablename__ = "reminders"
    contact_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("contacts.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    next_expected_date: Mapped[date] = mapped_column(Date)
    frequency_type: Mapped[str] = mapped_column(
        String(20), default="one_time"
    )  # one_time, week, month, year
    frequency_number: Mapped[int] = mapped_column(Integer, default=1)
    last_triggered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[str] = mapped_column(String(20), default="active")


class StayInTouchConfig(VaultScopedModel):
    __tablename__ = "stay_in_touch_configs"
    contact_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("contacts.id"), unique=True
    )
    target_interval_days: Mapped[int] = mapped_column(Integer)
    last_contacted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
