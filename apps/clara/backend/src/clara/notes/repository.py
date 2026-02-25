import uuid
from collections.abc import Sequence

from sqlalchemy import func, or_, select

from clara.base.repository import BaseRepository
from clara.notes.models import Note


class NoteRepository(BaseRepository[Note]):
    model = Note

    async def list(
        self, *, offset: int = 0, limit: int = 50, q: str | None = None
    ) -> tuple[Sequence[Note], int]:
        count_stmt = (
            select(func.count())
            .select_from(Note)
            .where(Note.vault_id == self.vault_id)
            .where(Note.deleted_at.is_(None))
        )
        items_stmt = self._base_query()
        if q:
            pattern = f"%{q}%"
            filt = or_(Note.title.ilike(pattern), Note.body_markdown.ilike(pattern))
            count_stmt = count_stmt.where(filt)
            items_stmt = items_stmt.where(filt)
        total: int = (await self.session.execute(count_stmt)).scalar_one()
        items_stmt = (
            items_stmt.offset(offset).limit(limit).order_by(Note.created_at.desc())
        )
        result = await self.session.execute(items_stmt)
        return result.scalars().all(), total

    async def list_by_contact(
        self, contact_id: uuid.UUID, *, offset: int = 0, limit: int = 50
    ) -> tuple[Sequence[Note], int]:
        return await self.filtered_list(
            Note.contact_id == contact_id, offset=offset, limit=limit
        )

    async def list_by_activity(
        self, activity_id: uuid.UUID, *, offset: int = 0, limit: int = 50
    ) -> tuple[Sequence[Note], int]:
        return await self.filtered_list(
            Note.activity_id == activity_id, offset=offset, limit=limit
        )
