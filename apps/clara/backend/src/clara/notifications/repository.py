import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from clara.base.repository import BaseRepository
from clara.notifications.models import Notification


class NotificationRepository(BaseRepository[Notification]):
    model = Notification

    def __init__(
        self, session: AsyncSession, vault_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        super().__init__(session, vault_id)
        self.user_id = user_id

    def _base_query(self) -> Select[tuple[Notification]]:
        return super()._base_query().where(Notification.user_id == self.user_id)

    async def list_for_user(self, *, limit: int = 100) -> Sequence[Notification]:
        stmt = (
            self._base_query()
            .order_by(Notification.read.asc(), Notification.created_at.desc())
            .limit(limit)
        )
        return (await self.session.execute(stmt)).scalars().all()

    async def unread_count(self) -> int:
        stmt = (
            select(func.count())
            .select_from(Notification)
            .where(
                Notification.vault_id == self.vault_id,
                Notification.user_id == self.user_id,
                Notification.read.is_(False),
                Notification.deleted_at.is_(None),
            )
        )
        return (await self.session.execute(stmt)).scalar_one()

    async def mark_all_read(self) -> None:
        stmt = (
            update(Notification)
            .where(
                Notification.vault_id == self.vault_id,
                Notification.user_id == self.user_id,
                Notification.read.is_(False),
                Notification.deleted_at.is_(None),
            )
            .values(read=True)
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def clear_read(self) -> None:
        stmt = (
            update(Notification)
            .where(
                Notification.vault_id == self.vault_id,
                Notification.user_id == self.user_id,
                Notification.read.is_(True),
                Notification.deleted_at.is_(None),
            )
            .values(deleted_at=datetime.now(UTC))
        )
        await self.session.execute(stmt)
        await self.session.flush()
