import uuid
from collections.abc import Sequence

from clara.exceptions import NotFoundError
from clara.finance.gift_repository import GiftRepository
from clara.finance.gift_schemas import GiftCreate, GiftUpdate
from clara.finance.models import Gift


class GiftService:
    def __init__(self, repo: GiftRepository) -> None:
        self.repo = repo

    async def list_gifts(
        self, *, offset: int = 0, limit: int = 50
    ) -> tuple[Sequence[Gift], int]:
        return await self.repo.list(offset=offset, limit=limit)

    async def list_by_direction(
        self, direction: str, *, offset: int = 0, limit: int = 50
    ) -> tuple[Sequence[Gift], int]:
        return await self.repo.list_by_direction(
            direction, offset=offset, limit=limit
        )

    async def list_by_contact(
        self, contact_id: uuid.UUID, *, offset: int = 0, limit: int = 50
    ) -> tuple[Sequence[Gift], int]:
        return await self.repo.list_by_contact(
            contact_id, offset=offset, limit=limit
        )

    async def get_gift(self, gift_id: uuid.UUID) -> Gift:
        gift = await self.repo.get_by_id(gift_id)
        if gift is None:
            raise NotFoundError("Gift", gift_id)
        return gift

    async def create_gift(self, data: GiftCreate) -> Gift:
        return await self.repo.create(**data.model_dump())

    async def update_gift(self, gift_id: uuid.UUID, data: GiftUpdate) -> Gift:
        return await self.repo.update(
            gift_id, **data.model_dump(exclude_unset=True)
        )

    async def delete_gift(self, gift_id: uuid.UUID) -> None:
        await self.repo.soft_delete(gift_id)
