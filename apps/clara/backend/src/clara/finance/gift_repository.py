import uuid
from collections.abc import Sequence

from clara.base.repository import BaseRepository
from clara.finance.models import Gift


class GiftRepository(BaseRepository[Gift]):
    model = Gift

    async def list_by_direction(
        self, direction: str, *, offset: int = 0, limit: int = 50
    ) -> tuple[Sequence[Gift], int]:
        return await self.filtered_list(
            Gift.direction == direction, offset=offset, limit=limit
        )

    async def list_by_contact(
        self, contact_id: uuid.UUID, *, offset: int = 0, limit: int = 50
    ) -> tuple[Sequence[Gift], int]:
        return await self.filtered_list(
            Gift.contact_id == contact_id, offset=offset, limit=limit
        )
