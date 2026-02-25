import uuid
from collections.abc import Sequence
from datetime import date

from clara.exceptions import NotFoundError
from clara.reminders.models import Reminder, StayInTouchConfig
from clara.reminders.repository import ReminderRepository, StayInTouchRepository
from clara.reminders.schemas import (
    ReminderCreate,
    ReminderUpdate,
    StayInTouchCreateOrUpdate,
)


class ReminderService:
    def __init__(self, repo: ReminderRepository) -> None:
        self.repo = repo

    async def list_reminders(
        self, *, offset: int = 0, limit: int = 50
    ) -> tuple[Sequence[Reminder], int]:
        return await self.repo.list(offset=offset, limit=limit)

    async def list_by_status(
        self, status: str, *, offset: int = 0, limit: int = 50
    ) -> tuple[Sequence[Reminder], int]:
        return await self.repo.list_by_status(
            status, offset=offset, limit=limit
        )

    async def list_by_contact(
        self,
        contact_id: uuid.UUID,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[Sequence[Reminder], int]:
        return await self.repo.list_by_contact(
            contact_id, offset=offset, limit=limit
        )

    async def list_upcoming(
        self, as_of: date, *, offset: int = 0, limit: int = 50
    ) -> tuple[Sequence[Reminder], int]:
        return await self.repo.list_upcoming(
            as_of, offset=offset, limit=limit
        )

    async def list_overdue(
        self, as_of: date, *, offset: int = 0, limit: int = 50
    ) -> tuple[Sequence[Reminder], int]:
        return await self.repo.list_overdue(
            as_of, offset=offset, limit=limit
        )

    async def get_reminder(self, reminder_id: uuid.UUID) -> Reminder:
        reminder = await self.repo.get_by_id(reminder_id)
        if reminder is None:
            raise NotFoundError("Reminder", reminder_id)
        return reminder

    async def create_reminder(self, data: ReminderCreate) -> Reminder:
        return await self.repo.create(**data.model_dump())

    async def update_reminder(
        self, reminder_id: uuid.UUID, data: ReminderUpdate
    ) -> Reminder:
        return await self.repo.update(
            reminder_id, **data.model_dump(exclude_unset=True)
        )

    async def delete_reminder(self, reminder_id: uuid.UUID) -> None:
        await self.repo.soft_delete(reminder_id)


class StayInTouchService:
    def __init__(self, repo: StayInTouchRepository) -> None:
        self.repo = repo

    async def get_config(
        self, contact_id: uuid.UUID
    ) -> StayInTouchConfig | None:
        return await self.repo.get_by_contact(contact_id)

    async def set_config(
        self,
        contact_id: uuid.UUID,
        data: StayInTouchCreateOrUpdate,
    ) -> StayInTouchConfig:
        existing = await self.repo.get_by_contact(contact_id)
        if existing is not None:
            return await self.repo.update(
                existing.id, **data.model_dump(exclude_unset=True)
            )
        return await self.repo.create(
            contact_id=contact_id, **data.model_dump()
        )

    async def delete_config(self, contact_id: uuid.UUID) -> None:
        existing = await self.repo.get_by_contact(contact_id)
        if existing is None:
            raise NotFoundError("StayInTouchConfig", contact_id)
        await self.repo.soft_delete(existing.id)
