from collections.abc import Sequence
from datetime import date

from sqlalchemy import Select, func, select
from sqlalchemy.orm import selectinload

from clara.base.repository import BaseRepository
from clara.journal.models import JournalEntry


class JournalEntryRepository(BaseRepository[JournalEntry]):
    model = JournalEntry

    def _base_query(self) -> Select[tuple[JournalEntry]]:
        return (
            super()._base_query()
            .options(selectinload(JournalEntry.contacts))
        )

    async def list_by_date_range(
        self, start: date, end: date, *, offset: int = 0, limit: int = 50
    ) -> tuple[Sequence[JournalEntry], int]:
        base = self._base_query().where(
            JournalEntry.entry_date >= start,
            JournalEntry.entry_date <= end,
        )
        count_stmt = (
            select(func.count())
            .select_from(JournalEntry)
            .where(JournalEntry.vault_id == self.vault_id)
            .where(JournalEntry.deleted_at.is_(None))
            .where(JournalEntry.entry_date >= start)
            .where(JournalEntry.entry_date <= end)
        )
        total = (await self.session.execute(count_stmt)).scalar_one()
        items = (
            await self.session.execute(
                base.order_by(JournalEntry.entry_date.desc())
                .offset(offset)
                .limit(limit)
            )
        ).scalars().unique().all()
        return items, total

    async def list(
        self, *, offset: int = 0, limit: int = 50
    ) -> tuple[Sequence[JournalEntry], int]:
        count_stmt = (
            select(func.count())
            .select_from(JournalEntry)
            .where(JournalEntry.vault_id == self.vault_id)
            .where(JournalEntry.deleted_at.is_(None))
        )
        total = (await self.session.execute(count_stmt)).scalar_one()
        items_stmt = (
            self._base_query()
            .offset(offset)
            .limit(limit)
            .order_by(JournalEntry.entry_date.desc())
        )
        result = await self.session.execute(items_stmt)
        return result.scalars().unique().all(), total
