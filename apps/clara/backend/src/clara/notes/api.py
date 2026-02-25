import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from clara.base.schema import PaginatedResponse, PaginationMeta
from clara.deps import CurrentUser, Db, VaultAccess
from clara.notes.repository import NoteRepository
from clara.notes.schemas import NoteCreate, NoteRead, NoteUpdate
from clara.notes.service import NoteService
from clara.pagination import PaginationParams

router = APIRouter()


def get_note_service(
    vault_id: uuid.UUID, db: Db, _access: VaultAccess
) -> NoteService:
    repo = NoteRepository(session=db, vault_id=vault_id)
    return NoteService(repo=repo)


NoteSvc = Annotated[NoteService, Depends(get_note_service)]


@router.get("", response_model=PaginatedResponse[NoteRead])
async def list_notes(
    svc: NoteSvc,
    pagination: PaginationParams = Depends(),
    contact_id: uuid.UUID | None = None,
    activity_id: uuid.UUID | None = None,
    q: str | None = None,
) -> PaginatedResponse[NoteRead]:
    if contact_id is not None:
        items, total = await svc.list_by_contact(
            contact_id, offset=pagination.offset, limit=pagination.limit
        )
    elif activity_id is not None:
        items, total = await svc.list_by_activity(
            activity_id, offset=pagination.offset, limit=pagination.limit
        )
    else:
        items, total = await svc.list_notes(
            offset=pagination.offset, limit=pagination.limit, q=q
        )
    return PaginatedResponse(
        items=[NoteRead.model_validate(n) for n in items],
        meta=PaginationMeta(
            total=total, offset=pagination.offset, limit=pagination.limit
        ),
    )


@router.get("/{note_id}", response_model=NoteRead)
async def get_note(note_id: uuid.UUID, svc: NoteSvc) -> NoteRead:
    return NoteRead.model_validate(await svc.get_note(note_id))


@router.post("", response_model=NoteRead, status_code=201)
async def create_note(body: NoteCreate, svc: NoteSvc, user: CurrentUser) -> NoteRead:
    return NoteRead.model_validate(
        await svc.create_note(body, created_by_id=user.id)
    )


@router.patch("/{note_id}", response_model=NoteRead)
async def update_note(note_id: uuid.UUID, body: NoteUpdate, svc: NoteSvc) -> NoteRead:
    return NoteRead.model_validate(await svc.update_note(note_id, body))


@router.delete("/{note_id}", status_code=204)
async def delete_note(note_id: uuid.UUID, svc: NoteSvc) -> None:
    await svc.delete_note(note_id)
