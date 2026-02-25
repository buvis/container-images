import uuid
from collections.abc import Sequence

from sqlalchemy import func, select

from clara.base.repository import BaseRepository
from clara.files.models import File, FileLink


class FileRepository(BaseRepository[File]):
    model = File

    async def list(
        self, *, offset: int = 0, limit: int = 50, q: str | None = None
    ) -> tuple[Sequence[File], int]:
        count_stmt = (
            select(func.count())
            .select_from(File)
            .where(File.vault_id == self.vault_id)
            .where(File.deleted_at.is_(None))
        )
        items_stmt = self._base_query()
        if q:
            pattern = f"%{q}%"
            count_stmt = count_stmt.where(File.filename.ilike(pattern))
            items_stmt = items_stmt.where(File.filename.ilike(pattern))
        total: int = (await self.session.execute(count_stmt)).scalar_one()
        items_stmt = (
            items_stmt.offset(offset).limit(limit).order_by(File.created_at.desc())
        )
        result = await self.session.execute(items_stmt)
        return result.scalars().all(), total


class FileLinkRepository(BaseRepository[FileLink]):
    model = FileLink

    async def list_by_file(self, file_id: uuid.UUID) -> list[FileLink]:
        stmt = self._base_query().where(FileLink.file_id == file_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_target(
        self, target_type: str, target_id: uuid.UUID
    ) -> list[FileLink]:
        stmt = (
            self._base_query()
            .where(FileLink.target_type == target_type)
            .where(FileLink.target_id == target_id)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
