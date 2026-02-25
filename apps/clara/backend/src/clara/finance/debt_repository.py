import uuid
from collections.abc import Sequence

from clara.base.repository import BaseRepository
from clara.finance.models import Debt


class DebtRepository(BaseRepository[Debt]):
    model = Debt

    async def list_settled(
        self, settled: bool, *, offset: int = 0, limit: int = 50
    ) -> tuple[Sequence[Debt], int]:
        return await self.filtered_list(
            Debt.settled == settled, offset=offset, limit=limit
        )

    async def list_by_contact(
        self, contact_id: uuid.UUID, *, offset: int = 0, limit: int = 50
    ) -> tuple[Sequence[Debt], int]:
        return await self.filtered_list(
            Debt.contact_id == contact_id, offset=offset, limit=limit
        )

    async def list_by_direction(
        self, direction: str, *, offset: int = 0, limit: int = 50
    ) -> tuple[Sequence[Debt], int]:
        return await self.filtered_list(
            Debt.direction == direction, offset=offset, limit=limit
        )
