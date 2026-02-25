import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from clara.activities.models import Activity, ActivityParticipant, ActivityType
from clara.contacts.models import (
    Address,
    Contact,
    ContactMethod,
    ContactRelationship,
    Pet,
    Tag,
)
from clara.finance.models import Debt, Gift
from clara.journal.models import JournalEntry, JournalEntryContact
from clara.notes.models import Note
from clara.reminders.models import Reminder, StayInTouchConfig
from clara.tasks.models import Task


def _serialize(obj: Any) -> dict[str, Any]:
    result = {}
    for col in obj.__table__.columns:
        val = getattr(obj, col.name)
        if isinstance(val, (datetime, date)):
            val = val.isoformat()
        elif isinstance(val, uuid.UUID):
            val = str(val)
        elif isinstance(val, Decimal):
            val = float(val)
        result[col.name] = val
    return result


async def _fetch_all(
    session: AsyncSession, model: Any, vault_id: uuid.UUID
) -> list[dict[str, Any]]:
    stmt = (
        select(model)
        .where(model.vault_id == vault_id)
        .where(model.deleted_at.is_(None))
    )
    result = await session.execute(stmt)
    return [_serialize(row) for row in result.scalars().all()]


async def export_vault_json(
    session: AsyncSession, vault_id: uuid.UUID
) -> dict[str, Any]:
    return {
        "vault_id": str(vault_id),
        "contacts": await _fetch_all(session, Contact, vault_id),
        "contact_methods": await _fetch_all(session, ContactMethod, vault_id),
        "addresses": await _fetch_all(session, Address, vault_id),
        "contact_relationships": await _fetch_all(
            session, ContactRelationship, vault_id
        ),
        "tags": await _fetch_all(session, Tag, vault_id),
        "pets": await _fetch_all(session, Pet, vault_id),
        "activity_types": await _fetch_all(session, ActivityType, vault_id),
        "activities": await _fetch_all(session, Activity, vault_id),
        "activity_participants": await _fetch_all(
            session, ActivityParticipant, vault_id
        ),
        "notes": await _fetch_all(session, Note, vault_id),
        "reminders": await _fetch_all(session, Reminder, vault_id),
        "stay_in_touch_configs": await _fetch_all(
            session, StayInTouchConfig, vault_id
        ),
        "tasks": await _fetch_all(session, Task, vault_id),
        "journal_entries": await _fetch_all(session, JournalEntry, vault_id),
        "journal_entry_contacts": await _fetch_all(
            session, JournalEntryContact, vault_id
        ),
        "gifts": await _fetch_all(session, Gift, vault_id),
        "debts": await _fetch_all(session, Debt, vault_id),
    }
