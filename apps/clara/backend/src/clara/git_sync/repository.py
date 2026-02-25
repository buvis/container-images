import uuid
from collections.abc import Sequence

from sqlalchemy import Select, func, select
from sqlalchemy.orm import selectinload

from clara.base.repository import BaseRepository
from clara.git_sync.models import GitSyncConfig, GitSyncMapping


class GitSyncConfigRepository(BaseRepository[GitSyncConfig]):
    model = GitSyncConfig

    def _base_query(self) -> Select[tuple[GitSyncConfig]]:
        return super()._base_query().options(selectinload(GitSyncConfig.mappings))

    async def get_for_vault(self) -> GitSyncConfig | None:
        """Get the single config for this vault (one per vault)."""
        stmt = self._base_query()
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class GitSyncMappingRepository(BaseRepository[GitSyncMapping]):
    model = GitSyncMapping

    async def get_by_contact(
        self, config_id: uuid.UUID, contact_id: uuid.UUID
    ) -> GitSyncMapping | None:
        stmt = (
            self._base_query()
            .where(GitSyncMapping.config_id == config_id)
            .where(GitSyncMapping.contact_id == contact_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_markdown_id(
        self, config_id: uuid.UUID, markdown_id: str
    ) -> GitSyncMapping | None:
        stmt = (
            self._base_query()
            .where(GitSyncMapping.config_id == config_id)
            .where(GitSyncMapping.markdown_id == markdown_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_config(self, config_id: uuid.UUID) -> Sequence[GitSyncMapping]:
        stmt = self._base_query().where(GitSyncMapping.config_id == config_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count_by_config(self, config_id: uuid.UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(GitSyncMapping)
            .where(GitSyncMapping.vault_id == self.vault_id)
            .where(GitSyncMapping.config_id == config_id)
            .where(GitSyncMapping.deleted_at.is_(None))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()
