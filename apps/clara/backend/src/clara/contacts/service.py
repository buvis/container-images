import uuid
from collections.abc import Sequence
from datetime import date

from clara.contacts.models import Contact
from clara.contacts.repository import ContactRepository
from clara.contacts.schemas import ContactCreate, ContactUpdate
from clara.exceptions import NotFoundError


class ContactService:
    def __init__(self, repo: ContactRepository) -> None:
        self.repo = repo

    async def list_contacts(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
        q: str | None = None,
        tag_ids: list[uuid.UUID] | None = None,
        favorites: bool | None = None,
        birthday_from: date | None = None,
        birthday_to: date | None = None,
    ) -> tuple[Sequence[Contact], int]:
        return await self.repo.list_filtered(
            offset=offset, limit=limit, q=q, tag_ids=tag_ids,
            favorites=favorites, birthday_from=birthday_from,
            birthday_to=birthday_to,
        )

    async def get_contact(self, contact_id: uuid.UUID) -> Contact:
        contact = await self.repo.get_by_id(contact_id)
        if contact is None:
            raise NotFoundError("Contact", contact_id)
        return contact

    async def create_contact(self, data: ContactCreate) -> Contact:
        created = await self.repo.create(**data.model_dump())
        contact = await self.repo.get_by_id(created.id)
        if contact is None:
            raise NotFoundError("Contact", created.id)
        return contact

    async def update_contact(
        self, contact_id: uuid.UUID, data: ContactUpdate
    ) -> Contact:
        await self.repo.update(
            contact_id, **data.model_dump(exclude_unset=True)
        )
        contact = await self.repo.get_by_id(contact_id)
        if contact is None:
            raise NotFoundError("Contact", contact_id)
        return contact

    async def delete_contact(self, contact_id: uuid.UUID) -> None:
        await self.repo.soft_delete(contact_id)

    async def search_contacts(
        self, query: str, *, offset: int = 0, limit: int = 50
    ) -> tuple[Sequence[Contact], int]:
        return await self.repo.search(query, offset=offset, limit=limit)
