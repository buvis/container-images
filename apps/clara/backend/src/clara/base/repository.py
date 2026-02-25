import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any, TypeVar

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from clara.base.model import VaultScopedModel
from clara.exceptions import NotFoundError

ModelT = TypeVar("ModelT", bound=VaultScopedModel)


class BaseRepository[ModelT: VaultScopedModel]:
    model: type[ModelT]

    def __init__(self, session: AsyncSession, vault_id: uuid.UUID) -> None:
        self.session = session
        self.vault_id = vault_id

    def _base_query(self) -> Select[tuple[ModelT]]:
        return (
            select(self.model)
            .where(self.model.vault_id == self.vault_id)
            .where(self.model.deleted_at.is_(None))
        )

    async def get_by_id(self, id: uuid.UUID) -> ModelT | None:
        stmt = self._base_query().where(self.model.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self, *, offset: int = 0, limit: int = 50
    ) -> tuple[Sequence[ModelT], int]:
        count_stmt = (
            select(func.count())
            .select_from(self.model)
            .where(self.model.vault_id == self.vault_id)
            .where(self.model.deleted_at.is_(None))
        )
        total = (await self.session.execute(count_stmt)).scalar_one()
        items_stmt = (
            self._base_query()
            .offset(offset)
            .limit(limit)
            .order_by(self.model.created_at.desc())
        )
        result = await self.session.execute(items_stmt)
        return result.scalars().all(), total

    async def filtered_list(
        self,
        *filters: Any,
        order_by: Any = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[Sequence[ModelT], int]:
        base = self._base_query()
        for f in filters:
            base = base.where(f)
        count_stmt = select(func.count()).select_from(base.subquery())
        total: int = (await self.session.execute(count_stmt)).scalar_one()
        items_stmt = base.order_by(
            order_by if order_by is not None else self.model.created_at.desc()
        ).offset(offset).limit(limit)
        result = await self.session.execute(items_stmt)
        return result.scalars().all(), total

    async def create(self, **kwargs: Any) -> ModelT:
        obj = self.model(vault_id=self.vault_id, **kwargs)
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def update(self, id: uuid.UUID, **kwargs: Any) -> ModelT:
        obj = await self.get_by_id(id)
        if obj is None:
            raise NotFoundError(self.model.__name__, id)
        for key, value in kwargs.items():
            setattr(obj, key, value)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def soft_delete(self, id: uuid.UUID) -> None:
        obj = await self.get_by_id(id)
        if obj is None:
            raise NotFoundError(self.model.__name__, id)
        obj.deleted_at = datetime.now(UTC)
        await self.session.flush()
