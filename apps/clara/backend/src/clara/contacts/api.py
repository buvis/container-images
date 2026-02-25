import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from clara.activities.repository import ActivityRepository
from clara.activities.schemas import ActivityRead
from clara.base.schema import PaginatedResponse, PaginationMeta
from clara.contacts.repository import ContactRepository
from clara.contacts.schemas import ContactCreate, ContactRead, ContactUpdate
from clara.contacts.service import ContactService
from clara.deps import Db, VaultAccess
from clara.pagination import PaginationParams

router = APIRouter()


def get_contact_service(
    vault_id: uuid.UUID, db: Db, _access: VaultAccess
) -> ContactService:
    repo = ContactRepository(session=db, vault_id=vault_id)
    return ContactService(repo=repo)


ContactSvc = Annotated[ContactService, Depends(get_contact_service)]


@router.get("", response_model=PaginatedResponse[ContactRead])
async def list_contacts(
    svc: ContactSvc,
    pagination: PaginationParams = Depends(),
    q: str | None = None,
    tags: str | None = Query(None, description="Comma-separated tag UUIDs"),
    favorites: bool | None = None,
    birthday_from: date | None = None,
    birthday_to: date | None = None,
) -> PaginatedResponse[ContactRead]:
    tag_ids = (
        [uuid.UUID(t.strip()) for t in tags.split(",") if t.strip()]
        if tags
        else None
    )
    items, total = await svc.list_contacts(
        offset=pagination.offset,
        limit=pagination.limit,
        q=q,
        tag_ids=tag_ids,
        favorites=favorites,
        birthday_from=birthday_from,
        birthday_to=birthday_to,
    )
    return PaginatedResponse(
        items=[ContactRead.model_validate(c) for c in items],
        meta=PaginationMeta(
            total=total, offset=pagination.offset, limit=pagination.limit
        ),
    )


@router.get("/{contact_id}", response_model=ContactRead)
async def get_contact(contact_id: uuid.UUID, svc: ContactSvc) -> ContactRead:
    return ContactRead.model_validate(await svc.get_contact(contact_id))


@router.post("", response_model=ContactRead, status_code=201)
async def create_contact(body: ContactCreate, svc: ContactSvc) -> ContactRead:
    return ContactRead.model_validate(await svc.create_contact(body))


@router.patch("/{contact_id}", response_model=ContactRead)
async def update_contact(
    contact_id: uuid.UUID, body: ContactUpdate, svc: ContactSvc
) -> ContactRead:
    return ContactRead.model_validate(
        await svc.update_contact(contact_id, body)
    )


@router.delete("/{contact_id}", status_code=204)
async def delete_contact(contact_id: uuid.UUID, svc: ContactSvc) -> None:
    await svc.delete_contact(contact_id)


@router.get(
    "/{contact_id}/activities", response_model=PaginatedResponse[ActivityRead]
)
async def list_contact_activities(
    vault_id: uuid.UUID,
    contact_id: uuid.UUID,
    db: Db,
    _access: VaultAccess,
    pagination: PaginationParams = Depends(),
) -> PaginatedResponse[ActivityRead]:
    repo = ActivityRepository(session=db, vault_id=vault_id)
    items, total = await repo.list_by_contact(
        contact_id, offset=pagination.offset, limit=pagination.limit
    )
    return PaginatedResponse(
        items=[ActivityRead.model_validate(a) for a in items],
        meta=PaginationMeta(
            total=total, offset=pagination.offset, limit=pagination.limit
        ),
    )
