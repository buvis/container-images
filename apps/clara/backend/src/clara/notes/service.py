import uuid
from collections.abc import Sequence

from clara.exceptions import NotFoundError
from clara.notes.models import Note
from clara.notes.repository import NoteRepository
from clara.notes.schemas import NoteCreate, NoteUpdate


class NoteService:
    def __init__(self, repo: NoteRepository) -> None:
        self.repo = repo

    async def list_notes(
        self, *, offset: int = 0, limit: int = 50, q: str | None = None
    ) -> tuple[Sequence[Note], int]:
        return await self.repo.list(offset=offset, limit=limit, q=q)

    async def list_by_contact(
        self,
        contact_id: uuid.UUID,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[Sequence[Note], int]:
        return await self.repo.list_by_contact(
            contact_id, offset=offset, limit=limit
        )

    async def list_by_activity(
        self,
        activity_id: uuid.UUID,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[Sequence[Note], int]:
        return await self.repo.list_by_activity(
            activity_id, offset=offset, limit=limit
        )

    async def get_note(self, note_id: uuid.UUID) -> Note:
        note = await self.repo.get_by_id(note_id)
        if note is None:
            raise NotFoundError("Note", note_id)
        return note

    async def create_note(self, data: NoteCreate, *, created_by_id: uuid.UUID) -> Note:
        return await self.repo.create(**data.model_dump(), created_by_id=created_by_id)

    async def update_note(
        self, note_id: uuid.UUID, data: NoteUpdate
    ) -> Note:
        return await self.repo.update(
            note_id, **data.model_dump(exclude_unset=True)
        )

    async def delete_note(self, note_id: uuid.UUID) -> None:
        await self.repo.soft_delete(note_id)
