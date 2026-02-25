import sys
import uuid
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import Row, func, select
from sqlalchemy.orm import Session

from clara.activities.models import Activity
from clara.auth.models import User, Vault, VaultMembership
from clara.email.sender import get_sender
from clara.jobs.sync_db import get_sync_session
from clara.reminders.models import Reminder, StayInTouchConfig
from clara.tasks.models import Task


@dataclass
class UserDigest:
    email: str
    name: str
    items: list[str] = field(default_factory=list)


def _membership_rows(
    session: Session,
) -> Sequence[Row[tuple[uuid.UUID, str, str, uuid.UUID, str]]]:
    stmt = (
        select(User.id, User.email, User.name, Vault.id, Vault.name)
        .join(
            VaultMembership,
            VaultMembership.user_id == User.id,
        )
        .join(Vault, Vault.id == VaultMembership.vault_id)
        .where(
            User.deleted_at.is_(None),
            User.is_active.is_(True),
            Vault.deleted_at.is_(None),
            VaultMembership.deleted_at.is_(None),
        )
    )
    return session.execute(stmt).all()


def _build_digest_html(user_name: str, items: list[str], title: str) -> str:
    from html import escape

    list_items = "".join(f"<li>{escape(item)}</li>" for item in items)
    greeting = escape(user_name) if user_name else "there"
    return (
        "<html><body>"
        f"<p>Hi {greeting},</p>"
        f"<p>{escape(title)}</p>"
        f"<ul>{list_items}</ul>"
        "<p>– CLARA</p>"
        "</body></html>"
    )


def daily_digest() -> None:
    session = get_sync_session()
    try:
        sender = get_sender()
        today = date.today()
        reminders_stmt = (
            select(Reminder.vault_id, func.count(Reminder.id))
            .where(
                Reminder.deleted_at.is_(None),
                Reminder.status == "active",
                Reminder.next_expected_date <= today,
            )
            .group_by(Reminder.vault_id)
        )
        reminder_counts: dict[uuid.UUID, int] = dict(
            session.execute(reminders_stmt).all()  # type: ignore[arg-type]
        )
        tasks_stmt = (
            select(Task.vault_id, func.count(Task.id))
            .where(
                Task.deleted_at.is_(None),
                Task.due_date.is_not(None),
                Task.due_date < today,
                Task.status.notin_(("completed", "done")),
            )
            .group_by(Task.vault_id)
        )
        overdue_task_counts: dict[uuid.UUID, int] = dict(
            session.execute(tasks_stmt).all()  # type: ignore[arg-type]
        )
        summaries: dict[uuid.UUID, UserDigest] = {}
        for user_id, email, name, vault_id, vault_name in _membership_rows(session):
            due_reminders = reminder_counts.get(vault_id, 0)
            overdue_tasks = overdue_task_counts.get(vault_id, 0)
            if due_reminders == 0 and overdue_tasks == 0:
                continue
            user_summary = summaries.setdefault(
                user_id,
                UserDigest(email=email, name=name),
            )
            user_summary.items.append(
                f"{vault_name}: {due_reminders} active reminders due, "
                f"{overdue_tasks} overdue tasks."
            )
        for summary in summaries.values():
            if not summary.email or not summary.items:
                continue
            sender.send(
                summary.email,
                "Your CLARA daily digest",
                _build_digest_html(
                    summary.name,
                    summary.items,
                    "Here is your daily reminder and task summary.",
                ),
            )
    finally:
        session.close()


def weekly_summary() -> None:
    session = get_sync_session()
    try:
        sender = get_sender()
        now = datetime.now(UTC)
        week_ago = now - timedelta(days=7)
        today = now.date()
        activity_stmt = (
            select(Activity.vault_id, func.count(Activity.id))
            .where(
                Activity.deleted_at.is_(None),
                Activity.happened_at >= week_ago,
            )
            .group_by(Activity.vault_id)
        )
        activity_counts: dict[uuid.UUID, int] = dict(
            session.execute(activity_stmt).all()  # type: ignore[arg-type]
        )
        overdue_stay_in_touch_counts: dict[uuid.UUID, int] = {}
        configs = (
            session.execute(
                select(
                    StayInTouchConfig.vault_id,
                    StayInTouchConfig.target_interval_days,
                    StayInTouchConfig.last_contacted_at,
                ).where(StayInTouchConfig.deleted_at.is_(None))
            )
            .all()
        )
        for vault_id, target_interval_days, last_contacted_at in configs:
            if last_contacted_at is None:
                overdue = True
            else:
                days_since = (today - last_contacted_at.date()).days
                overdue = days_since >= target_interval_days
            if overdue:
                overdue_stay_in_touch_counts[vault_id] = (
                    overdue_stay_in_touch_counts.get(vault_id, 0) + 1
                )
        summaries: dict[uuid.UUID, UserDigest] = {}
        for user_id, email, name, vault_id, vault_name in _membership_rows(session):
            recent_activities = activity_counts.get(vault_id, 0)
            overdue_contacts = overdue_stay_in_touch_counts.get(vault_id, 0)
            if recent_activities == 0 and overdue_contacts == 0:
                continue
            user_summary = summaries.setdefault(
                user_id,
                UserDigest(email=email, name=name),
            )
            user_summary.items.append(
                f"{vault_name}: {recent_activities} recent activities, "
                f"{overdue_contacts} contacts overdue for stay in touch."
            )
        for summary in summaries.values():
            if not summary.email or not summary.items:
                continue
            sender.send(
                summary.email,
                "Your CLARA weekly summary",
                _build_digest_html(
                    summary.name,
                    summary.items,
                    "Here is your weekly activity and relationship summary.",
                ),
            )
    finally:
        session.close()


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "daily"
    if command == "daily":
        daily_digest()
    elif command == "weekly":
        weekly_summary()
    else:
        raise SystemExit("Usage: python -m clara.jobs.digest [daily|weekly]")
