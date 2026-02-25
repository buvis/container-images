import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Boolean, Date, ForeignKey, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from clara.base.model import VaultScopedModel


class Gift(VaultScopedModel):
    __tablename__ = "gifts"
    contact_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("contacts.id")
    )
    direction: Mapped[str] = mapped_column(String(20))  # given, received, idea
    name: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    status: Mapped[str] = mapped_column(String(20), default="idea")
    link: Mapped[str | None] = mapped_column(String(2000))


class Debt(VaultScopedModel):
    __tablename__ = "debts"
    contact_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("contacts.id")
    )
    direction: Mapped[str] = mapped_column(String(20))  # you_owe, owed_to_you
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    due_date: Mapped[date | None] = mapped_column(Date)
    settled: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text)
