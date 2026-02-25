import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from clara.base.schema import PaginatedResponse, PaginationMeta
from clara.deps import CurrentUser, Db, VaultAccess
from clara.journal.repository import JournalEntryRepository
from clara.journal.schemas import (
    JournalEntryCreate,
    JournalEntryRead,
    JournalEntryUpdate,
)
from clara.journal.service import JournalService
from clara.pagination import PaginationParams

router = APIRouter()


def get_journal_service(
    vault_id: uuid.UUID, db: Db, _access: VaultAccess, user: CurrentUser
) -> JournalService:
    repo = JournalEntryRepository(session=db, vault_id=vault_id)
    return JournalService(repo=repo, user_id=user.id)


JournalSvc = Annotated[JournalService, Depends(get_journal_service)]


@router.get("", response_model=PaginatedResponse[JournalEntryRead])
async def list_entries(
    svc: JournalSvc,
    pagination: PaginationParams = Depends(),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
) -> PaginatedResponse[JournalEntryRead]:
    if date_from and date_to:
        items, total = await svc.list_by_date_range(
            date_from,
            date_to,
            offset=pagination.offset,
            limit=pagination.limit,
        )
    else:
        items, total = await svc.list_entries(
            offset=pagination.offset, limit=pagination.limit
        )
    return PaginatedResponse(
        items=[JournalEntryRead.model_validate(e) for e in items],
        meta=PaginationMeta(
            total=total, offset=pagination.offset, limit=pagination.limit
        ),
    )


@router.get("/{entry_id}", response_model=JournalEntryRead)
async def get_entry(entry_id: uuid.UUID, svc: JournalSvc) -> JournalEntryRead:
    return JournalEntryRead.model_validate(await svc.get_entry(entry_id))


@router.post("", response_model=JournalEntryRead, status_code=201)
async def create_entry(body: JournalEntryCreate, svc: JournalSvc) -> JournalEntryRead:
    return JournalEntryRead.model_validate(await svc.create_entry(body))


@router.patch("/{entry_id}", response_model=JournalEntryRead)
async def update_entry(
    entry_id: uuid.UUID, body: JournalEntryUpdate, svc: JournalSvc
) -> JournalEntryRead:
    return JournalEntryRead.model_validate(
        await svc.update_entry(entry_id, body)
    )


@router.delete("/{entry_id}", status_code=204)
async def delete_entry(entry_id: uuid.UUID, svc: JournalSvc) -> None:
    await svc.delete_entry(entry_id)
