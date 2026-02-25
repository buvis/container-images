import uuid
from collections.abc import Sequence

from sqlalchemy import Select, func, select
from sqlalchemy.orm import selectinload

from clara.base.repository import BaseRepository
from clara.dav_sync.models import DavSyncAccount, DavSyncMapping


class DavSyncAccountRepository(BaseRepository[DavSyncAccount]):
    model = DavSyncAccount

    def _base_query(self) -> Select[tuple[DavSyncAccount]]:
        return super()._base_query().options(selectinload(DavSyncAccount.mappings))


class DavSyncMappingRepository(BaseRepository[DavSyncMapping]):
    model = DavSyncMapping

    async def get_by_account_and_entity(
        self, account_id: uuid.UUID, entity_type: str, local_id: uuid.UUID
    ) -> DavSyncMapping | None:
        stmt = (
            self._base_query()
            .where(DavSyncMapping.account_id == account_id)
            .where(DavSyncMapping.entity_type == entity_type)
            .where(DavSyncMapping.local_id == local_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_remote_uid(
        self, account_id: uuid.UUID, entity_type: str, remote_uid: str
    ) -> DavSyncMapping | None:
        stmt = (
            self._base_query()
            .where(DavSyncMapping.account_id == account_id)
            .where(DavSyncMapping.entity_type == entity_type)
            .where(DavSyncMapping.remote_uid == remote_uid)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_account(
        self, account_id: uuid.UUID, entity_type: str | None = None
    ) -> Sequence[DavSyncMapping]:
        stmt = self._base_query().where(DavSyncMapping.account_id == account_id)
        if entity_type:
            stmt = stmt.where(DavSyncMapping.entity_type == entity_type)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count_by_account(self, account_id: uuid.UUID) -> dict[str, int]:
        stmt = (
            select(DavSyncMapping.entity_type, func.count())
            .where(DavSyncMapping.vault_id == self.vault_id)
            .where(DavSyncMapping.account_id == account_id)
            .where(DavSyncMapping.deleted_at.is_(None))
            .group_by(DavSyncMapping.entity_type)
        )
        result = await self.session.execute(stmt)
        return dict(result.all())  # type: ignore[arg-type]
