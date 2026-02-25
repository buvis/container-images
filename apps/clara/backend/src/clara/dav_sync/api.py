"""DAV sync REST endpoints."""

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends

from clara.dav_sync.repository import DavSyncAccountRepository, DavSyncMappingRepository
from clara.dav_sync.schemas import (
    DavSyncAccountCreate,
    DavSyncAccountRead,
    DavSyncAccountUpdate,
    DavSyncStatusRead,
)
from clara.dav_sync.service import DavSyncService
from clara.deps import Db, VaultAccess

router = APIRouter()


def get_dav_sync_service(
    vault_id: uuid.UUID, db: Db, _access: VaultAccess
) -> DavSyncService:
    account_repo = DavSyncAccountRepository(session=db, vault_id=vault_id)
    mapping_repo = DavSyncMappingRepository(session=db, vault_id=vault_id)
    return DavSyncService(account_repo=account_repo, mapping_repo=mapping_repo)


DavSvc = Annotated[DavSyncService, Depends(get_dav_sync_service)]


@router.post("/accounts", response_model=DavSyncAccountRead, status_code=201)
async def create_account(
    body: DavSyncAccountCreate, svc: DavSvc
) -> DavSyncAccountRead:
    account = await svc.create_account(body)
    return DavSyncAccountRead.model_validate(account)


@router.get("/accounts", response_model=list[DavSyncAccountRead])
async def list_accounts(svc: DavSvc) -> list[DavSyncAccountRead]:
    accounts = await svc.list_accounts()
    return [DavSyncAccountRead.model_validate(a) for a in accounts]


@router.get("/accounts/{account_id}", response_model=DavSyncAccountRead)
async def get_account(account_id: uuid.UUID, svc: DavSvc) -> DavSyncAccountRead:
    account = await svc.get_account(account_id)
    return DavSyncAccountRead.model_validate(account)


@router.patch("/accounts/{account_id}", response_model=DavSyncAccountRead)
async def update_account(
    account_id: uuid.UUID, body: DavSyncAccountUpdate, svc: DavSvc
) -> DavSyncAccountRead:
    account = await svc.update_account(account_id, body)
    return DavSyncAccountRead.model_validate(account)


@router.delete("/accounts/{account_id}", status_code=204)
async def delete_account(account_id: uuid.UUID, svc: DavSvc) -> None:
    await svc.delete_account(account_id)


@router.post("/accounts/{account_id}/test")
async def test_connection(account_id: uuid.UUID, svc: DavSvc) -> dict[str, str | None]:
    return await svc.test_connection(account_id)


@router.post("/accounts/{account_id}/sync", status_code=202)
async def trigger_sync(account_id: uuid.UUID, svc: DavSvc) -> dict[str, str]:
    await svc.trigger_sync(account_id)
    return {"status": "queued"}


@router.get("/accounts/{account_id}/status", response_model=DavSyncStatusRead)
async def get_status(account_id: uuid.UUID, svc: DavSvc) -> dict[str, Any]:
    return await svc.get_status(account_id)
