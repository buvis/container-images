import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from clara.base.schema import PaginatedResponse, PaginationMeta
from clara.deps import Db, VaultAccess
from clara.finance.gift_repository import GiftRepository
from clara.finance.gift_schemas import GiftCreate, GiftRead, GiftUpdate
from clara.finance.gift_service import GiftService
from clara.pagination import PaginationParams

router = APIRouter()


def get_gift_service(
    vault_id: uuid.UUID, db: Db, _access: VaultAccess
) -> GiftService:
    repo = GiftRepository(session=db, vault_id=vault_id)
    return GiftService(repo=repo)


GiftSvc = Annotated[GiftService, Depends(get_gift_service)]


@router.get("", response_model=PaginatedResponse[GiftRead])
async def list_gifts(
    svc: GiftSvc,
    pagination: PaginationParams = Depends(),
    direction: str | None = Query(None),
    contact_id: uuid.UUID | None = Query(None),
) -> PaginatedResponse[GiftRead]:
    if direction:
        items, total = await svc.list_by_direction(
            direction, offset=pagination.offset, limit=pagination.limit
        )
    elif contact_id:
        items, total = await svc.list_by_contact(
            contact_id, offset=pagination.offset, limit=pagination.limit
        )
    else:
        items, total = await svc.list_gifts(
            offset=pagination.offset, limit=pagination.limit
        )
    return PaginatedResponse(
        items=[GiftRead.model_validate(g) for g in items],
        meta=PaginationMeta(
            total=total, offset=pagination.offset, limit=pagination.limit
        ),
    )


@router.get("/{gift_id}", response_model=GiftRead)
async def get_gift(gift_id: uuid.UUID, svc: GiftSvc) -> GiftRead:
    return GiftRead.model_validate(await svc.get_gift(gift_id))


@router.post("", response_model=GiftRead, status_code=201)
async def create_gift(body: GiftCreate, svc: GiftSvc) -> GiftRead:
    return GiftRead.model_validate(await svc.create_gift(body))


@router.patch("/{gift_id}", response_model=GiftRead)
async def update_gift(gift_id: uuid.UUID, body: GiftUpdate, svc: GiftSvc) -> GiftRead:
    return GiftRead.model_validate(await svc.update_gift(gift_id, body))


@router.delete("/{gift_id}", status_code=204)
async def delete_gift(gift_id: uuid.UUID, svc: GiftSvc) -> None:
    await svc.delete_gift(gift_id)
