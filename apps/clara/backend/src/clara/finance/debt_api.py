import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from clara.base.schema import PaginatedResponse, PaginationMeta
from clara.deps import Db, VaultAccess
from clara.finance.debt_repository import DebtRepository
from clara.finance.debt_schemas import DebtCreate, DebtRead, DebtUpdate
from clara.finance.debt_service import DebtService
from clara.pagination import PaginationParams

router = APIRouter()


def get_debt_service(
    vault_id: uuid.UUID, db: Db, _access: VaultAccess
) -> DebtService:
    repo = DebtRepository(session=db, vault_id=vault_id)
    return DebtService(repo=repo)


DebtSvc = Annotated[DebtService, Depends(get_debt_service)]


@router.get("", response_model=PaginatedResponse[DebtRead])
async def list_debts(
    svc: DebtSvc,
    pagination: PaginationParams = Depends(),
    settled: bool | None = Query(None),
    direction: str | None = Query(None),
    contact_id: uuid.UUID | None = Query(None),
) -> PaginatedResponse[DebtRead]:
    if settled is not None:
        items, total = await svc.list_settled(
            settled, offset=pagination.offset, limit=pagination.limit
        )
    elif direction:
        items, total = await svc.list_by_direction(
            direction, offset=pagination.offset, limit=pagination.limit
        )
    elif contact_id:
        items, total = await svc.list_by_contact(
            contact_id, offset=pagination.offset, limit=pagination.limit
        )
    else:
        items, total = await svc.list_debts(
            offset=pagination.offset, limit=pagination.limit
        )
    return PaginatedResponse(
        items=[DebtRead.model_validate(d) for d in items],
        meta=PaginationMeta(
            total=total, offset=pagination.offset, limit=pagination.limit
        ),
    )


@router.get("/{debt_id}", response_model=DebtRead)
async def get_debt(debt_id: uuid.UUID, svc: DebtSvc) -> DebtRead:
    return DebtRead.model_validate(await svc.get_debt(debt_id))


@router.post("", response_model=DebtRead, status_code=201)
async def create_debt(body: DebtCreate, svc: DebtSvc) -> DebtRead:
    return DebtRead.model_validate(await svc.create_debt(body))


@router.patch("/{debt_id}", response_model=DebtRead)
async def update_debt(debt_id: uuid.UUID, body: DebtUpdate, svc: DebtSvc) -> DebtRead:
    return DebtRead.model_validate(await svc.update_debt(debt_id, body))


@router.delete("/{debt_id}", status_code=204)
async def delete_debt(debt_id: uuid.UUID, svc: DebtSvc) -> None:
    await svc.delete_debt(debt_id)
