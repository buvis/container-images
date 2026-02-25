import uuid
from datetime import UTC, date, datetime, timedelta

from dateutil.relativedelta import relativedelta
from sqlalchemy import select
from sqlalchemy.orm import Session

from clara.auth.models import VaultMembership
from clara.jobs.sync_db import get_sync_session
from clara.notifications.models import Notification
from clara.reminders.models import Reminder, StayInTouchConfig


def _next_date(today: date, freq: str, n: int) -> date:
    if freq == "week":
        result = today + timedelta(weeks=n)
    elif freq == "month":
        result = today + relativedelta(months=n)
    elif freq == "year":
        result = today + relativedelta(years=n)
    else:
        result = today + timedelta(days=30 * n)
    return date(result.year, result.month, result.day)


def _notify_vault_members(
    session: Session,
    vault_id: uuid.UUID,
    title: str,
    body: str = "",
    link: str | None = None,
) -> None:
    members = (
        session.execute(
            select(VaultMembership).where(
                VaultMembership.vault_id == vault_id,
                VaultMembership.deleted_at.is_(None),
            )
        )
        .scalars()
        .all()
    )
    for m in members:
        session.add(
            Notification(
                user_id=m.user_id,
                vault_id=vault_id,
                title=title,
                body=body,
                link=link,
            )
        )


def evaluate_reminders() -> None:
    """Daily job: trigger due reminders, compute next occurrence for recurring."""
    session = get_sync_session()
    try:
        today = date.today()
        stmt = select(Reminder).where(
            Reminder.next_expected_date <= today,
            Reminder.status == "active",
            Reminder.deleted_at.is_(None),
        )
        reminders = session.execute(stmt).scalars().all()
        for r in reminders:
            r.last_triggered_at = datetime.now(UTC)
            _notify_vault_members(
                session, r.vault_id, f"Reminder: {r.title}",
                link=f"/vaults/{r.vault_id}/reminders",
            )
            if r.frequency_type == "one_time":
                r.status = "completed"
            else:
                r.next_expected_date = _next_date(
                    today, r.frequency_type, r.frequency_number
                )
        session.commit()
    finally:
        session.close()


def evaluate_stay_in_touch() -> None:
    """Daily job: create reminders for contacts not contacted recently."""
    session = get_sync_session()
    try:
        today = date.today()
        configs = (
            session.execute(
                select(StayInTouchConfig).where(
                    StayInTouchConfig.deleted_at.is_(None)
                )
            )
            .scalars()
            .all()
        )
        for config in configs:
            if config.last_contacted_at is None:
                overdue = True
            else:
                days_since = (today - config.last_contacted_at.date()).days
                overdue = days_since >= config.target_interval_days
            if overdue:
                existing = session.execute(
                    select(Reminder).where(
                        Reminder.contact_id == config.contact_id,
                        Reminder.vault_id == config.vault_id,
                        Reminder.status == "active",
                        Reminder.title.like("Stay in touch%"),
                    )
                ).scalar_one_or_none()
                if existing is None:
                    reminder = Reminder(
                        vault_id=config.vault_id,
                        contact_id=config.contact_id,
                        title="Stay in touch",
                        next_expected_date=today,
                        frequency_type="one_time",
                        status="active",
                    )
                    session.add(reminder)
                    _notify_vault_members(
                        session, config.vault_id, "Stay in touch overdue",
                        link=f"/vaults/{config.vault_id}/contacts/{config.contact_id}",
                    )
        session.commit()
    finally:
        session.close()
