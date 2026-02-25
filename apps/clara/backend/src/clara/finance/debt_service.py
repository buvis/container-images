import uuid
from collections.abc import Sequence

from clara.exceptions import NotFoundError
from clara.finance.debt_repository import DebtRepository
from clara.finance.debt_schemas import DebtCreate, DebtUpdate
from clara.finance.models import Debt


class DebtService:
    def __init__(self, repo: DebtRepository) -> None:
        self.repo = repo

    async def list_debts(
        self, *, offset: int = 0, limit: int = 50
    ) -> tuple[Sequence[Debt], int]:
        return await self.repo.list(offset=offset, limit=limit)

    async def list_settled(
        self, settled: bool, *, offset: int = 0, limit: int = 50
    ) -> tuple[Sequence[Debt], int]:
        return await self.repo.list_settled(
            settled, offset=offset, limit=limit
        )

    async def list_by_contact(
        self, contact_id: uuid.UUID, *, offset: int = 0, limit: int = 50
    ) -> tuple[Sequence[Debt], int]:
        return await self.repo.list_by_contact(
            contact_id, offset=offset, limit=limit
        )

    async def list_by_direction(
        self, direction: str, *, offset: int = 0, limit: int = 50
    ) -> tuple[Sequence[Debt], int]:
        return await self.repo.list_by_direction(
            direction, offset=offset, limit=limit
        )

    async def get_debt(self, debt_id: uuid.UUID) -> Debt:
        debt = await self.repo.get_by_id(debt_id)
        if debt is None:
            raise NotFoundError("Debt", debt_id)
        return debt

    async def create_debt(self, data: DebtCreate) -> Debt:
        return await self.repo.create(**data.model_dump())

    async def update_debt(self, debt_id: uuid.UUID, data: DebtUpdate) -> Debt:
        return await self.repo.update(
            debt_id, **data.model_dump(exclude_unset=True)
        )

    async def delete_debt(self, debt_id: uuid.UUID) -> None:
        await self.repo.soft_delete(debt_id)
