import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from clara.base.schema import PaginatedResponse, PaginationMeta
from clara.deps import Db, VaultAccess
from clara.pagination import PaginationParams
from clara.reminders.repository import ReminderRepository
from clara.reminders.schemas import ReminderCreate, ReminderRead, ReminderUpdate
from clara.reminders.service import ReminderService

router = APIRouter()


def get_reminder_service(
    vault_id: uuid.UUID, db: Db, _access: VaultAccess
) -> ReminderService:
    repo = ReminderRepository(session=db, vault_id=vault_id)
    return ReminderService(repo=repo)


ReminderSvc = Annotated[ReminderService, Depends(get_reminder_service)]


@router.get("", response_model=PaginatedResponse[ReminderRead])
async def list_reminders(
    svc: ReminderSvc,
    pagination: PaginationParams = Depends(),
    status: str | None = None,
    contact_id: uuid.UUID | None = None,
) -> PaginatedResponse[ReminderRead]:
    if contact_id is not None:
        items, total = await svc.list_by_contact(
            contact_id, offset=pagination.offset, limit=pagination.limit
        )
    elif status is not None:
        items, total = await svc.list_by_status(
            status, offset=pagination.offset, limit=pagination.limit
        )
    else:
        items, total = await svc.list_reminders(
            offset=pagination.offset, limit=pagination.limit
        )
    return PaginatedResponse(
        items=[ReminderRead.model_validate(r) for r in items],
        meta=PaginationMeta(
            total=total, offset=pagination.offset, limit=pagination.limit
        ),
    )


@router.get("/upcoming", response_model=PaginatedResponse[ReminderRead])
async def list_upcoming_reminders(
    svc: ReminderSvc,
    pagination: PaginationParams = Depends(),
    as_of: date = Query(default_factory=date.today),
) -> PaginatedResponse[ReminderRead]:
    items, total = await svc.list_upcoming(
        as_of, offset=pagination.offset, limit=pagination.limit
    )
    return PaginatedResponse(
        items=[ReminderRead.model_validate(r) for r in items],
        meta=PaginationMeta(
            total=total, offset=pagination.offset, limit=pagination.limit
        ),
    )


@router.get("/overdue", response_model=PaginatedResponse[ReminderRead])
async def list_overdue_reminders(
    svc: ReminderSvc,
    pagination: PaginationParams = Depends(),
    as_of: date = Query(default_factory=date.today),
) -> PaginatedResponse[ReminderRead]:
    items, total = await svc.list_overdue(
        as_of, offset=pagination.offset, limit=pagination.limit
    )
    return PaginatedResponse(
        items=[ReminderRead.model_validate(r) for r in items],
        meta=PaginationMeta(
            total=total, offset=pagination.offset, limit=pagination.limit
        ),
    )


@router.get("/{reminder_id}", response_model=ReminderRead)
async def get_reminder(reminder_id: uuid.UUID, svc: ReminderSvc) -> ReminderRead:
    return ReminderRead.model_validate(await svc.get_reminder(reminder_id))


@router.post("", response_model=ReminderRead, status_code=201)
async def create_reminder(body: ReminderCreate, svc: ReminderSvc) -> ReminderRead:
    return ReminderRead.model_validate(await svc.create_reminder(body))


@router.patch("/{reminder_id}", response_model=ReminderRead)
async def update_reminder(
    reminder_id: uuid.UUID, body: ReminderUpdate, svc: ReminderSvc
) -> ReminderRead:
    return ReminderRead.model_validate(
        await svc.update_reminder(reminder_id, body)
    )


@router.delete("/{reminder_id}", status_code=204)
async def delete_reminder(reminder_id: uuid.UUID, svc: ReminderSvc) -> None:
    await svc.delete_reminder(reminder_id)
