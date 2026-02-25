import uuid
from collections.abc import Sequence

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import selectinload

from clara.activities.models import Activity, ActivityParticipant, ActivityType
from clara.base.repository import BaseRepository


class ActivityTypeRepository(BaseRepository[ActivityType]):
    model = ActivityType


class ActivityRepository(BaseRepository[Activity]):
    model = Activity

    def _base_query(self) -> Select[tuple[Activity]]:
        return (
            super()
            ._base_query()
            .options(selectinload(Activity.participants))
        )

    async def list(
        self, *, offset: int = 0, limit: int = 50, q: str | None = None
    ) -> tuple[Sequence[Activity], int]:
        base_where = (
            select(func.count())
            .select_from(Activity)
            .where(Activity.vault_id == self.vault_id)
            .where(Activity.deleted_at.is_(None))
        )
        items_stmt = self._base_query()
        if q:
            pattern = f"%{q}%"
            filt = or_(
                Activity.title.ilike(pattern),
                Activity.description.ilike(pattern),
            )
            base_where = base_where.where(filt)
            items_stmt = items_stmt.where(filt)
        total: int = (await self.session.execute(base_where)).scalar_one()
        items_stmt = (
            items_stmt.order_by(Activity.happened_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(items_stmt)
        return result.scalars().all(), total

    async def list_by_contact(
        self, contact_id: uuid.UUID, *, offset: int = 0, limit: int = 50
    ) -> tuple[Sequence[Activity], int]:
        base = (
            self._base_query()
            .join(ActivityParticipant)
            .where(ActivityParticipant.contact_id == contact_id)
        )
        count_stmt = select(func.count()).select_from(base.subquery())
        total: int = (await self.session.execute(count_stmt)).scalar_one()
        items_stmt = (
            base.order_by(Activity.happened_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(items_stmt)
        return result.scalars().unique().all(), total


class ActivityParticipantRepository(BaseRepository[ActivityParticipant]):
    model = ActivityParticipant

    async def delete_by_activity(self, activity_id: uuid.UUID) -> None:
        stmt = (
            select(ActivityParticipant)
            .where(ActivityParticipant.activity_id == activity_id)
            .where(ActivityParticipant.vault_id == self.vault_id)
            .where(ActivityParticipant.deleted_at.is_(None))
        )
        result = await self.session.execute(stmt)
        for p in result.scalars().all():
            await self.session.delete(p)
        await self.session.flush()
