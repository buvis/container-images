import uuid
from collections.abc import Sequence
from datetime import date

from clara.base.repository import BaseRepository
from clara.reminders.models import Reminder, StayInTouchConfig


class ReminderRepository(BaseRepository[Reminder]):
    model = Reminder

    async def list_by_status(
        self,
        status: str,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[Sequence[Reminder], int]:
        return await self.filtered_list(
            Reminder.status == status,
            order_by=Reminder.next_expected_date.asc(),
            offset=offset,
            limit=limit,
        )

    async def list_by_contact(
        self,
        contact_id: uuid.UUID,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[Sequence[Reminder], int]:
        return await self.filtered_list(
            Reminder.contact_id == contact_id,
            order_by=Reminder.next_expected_date.asc(),
            offset=offset,
            limit=limit,
        )

    async def list_upcoming(
        self,
        as_of: date,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[Sequence[Reminder], int]:
        return await self.filtered_list(
            Reminder.status == "active",
            Reminder.next_expected_date >= as_of,
            order_by=Reminder.next_expected_date.asc(),
            offset=offset,
            limit=limit,
        )

    async def list_overdue(
        self,
        as_of: date,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[Sequence[Reminder], int]:
        return await self.filtered_list(
            Reminder.status == "active",
            Reminder.next_expected_date < as_of,
            order_by=Reminder.next_expected_date.asc(),
            offset=offset,
            limit=limit,
        )


class StayInTouchRepository(BaseRepository[StayInTouchConfig]):
    model = StayInTouchConfig

    async def get_by_contact(
        self, contact_id: uuid.UUID
    ) -> StayInTouchConfig | None:
        stmt = (
            self._base_query()
            .where(StayInTouchConfig.contact_id == contact_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
