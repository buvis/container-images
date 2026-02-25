import uuid
from collections.abc import Sequence
from datetime import date

from sqlalchemy import delete

from clara.exceptions import NotFoundError
from clara.journal.models import JournalEntry, JournalEntryContact
from clara.journal.repository import JournalEntryRepository
from clara.journal.schemas import JournalEntryCreate, JournalEntryUpdate


class JournalService:
    def __init__(self, repo: JournalEntryRepository, user_id: uuid.UUID) -> None:
        self.repo = repo
        self.user_id = user_id

    async def list_entries(
        self, *, offset: int = 0, limit: int = 50
    ) -> tuple[Sequence[JournalEntry], int]:
        return await self.repo.list(offset=offset, limit=limit)

    async def list_by_date_range(
        self, start: date, end: date, *, offset: int = 0, limit: int = 50
    ) -> tuple[Sequence[JournalEntry], int]:
        return await self.repo.list_by_date_range(
            start, end, offset=offset, limit=limit
        )

    async def get_entry(self, entry_id: uuid.UUID) -> JournalEntry:
        entry = await self.repo.get_by_id(entry_id)
        if entry is None:
            raise NotFoundError("JournalEntry", entry_id)
        return entry

    async def create_entry(self, data: JournalEntryCreate) -> JournalEntry:
        payload = data.model_dump(exclude={"contact_ids"})
        entry = await self.repo.create(**payload, created_by_id=self.user_id)
        await self._sync_contacts(entry.id, data.contact_ids)
        await self.repo.session.flush()
        return await self.get_entry(entry.id)

    async def update_entry(
        self, entry_id: uuid.UUID, data: JournalEntryUpdate
    ) -> JournalEntry:
        payload = data.model_dump(exclude={"contact_ids"}, exclude_unset=True)
        if payload:
            await self.repo.update(entry_id, **payload)
        if data.contact_ids is not None:
            await self._sync_contacts(entry_id, data.contact_ids)
        await self.repo.session.flush()
        return await self.get_entry(entry_id)

    async def delete_entry(self, entry_id: uuid.UUID) -> None:
        await self.repo.soft_delete(entry_id)

    async def _sync_contacts(
        self, entry_id: uuid.UUID, contact_ids: list[uuid.UUID]
    ) -> None:
        await self.repo.session.execute(
            delete(JournalEntryContact).where(
                JournalEntryContact.journal_entry_id == entry_id
            )
        )
        for cid in contact_ids:
            link = JournalEntryContact(
                vault_id=self.repo.vault_id,
                journal_entry_id=entry_id,
                contact_id=cid,
            )
            self.repo.session.add(link)
