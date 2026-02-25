"""Git sync REST endpoints."""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends

from clara.deps import Db, VaultAccess
from clara.git_sync.repository import GitSyncConfigRepository, GitSyncMappingRepository
from clara.git_sync.schemas import (
    GitSyncConfigCreate,
    GitSyncConfigRead,
    GitSyncConfigUpdate,
    GitSyncMappingRead,
    GitSyncStatusRead,
)
from clara.git_sync.service import GitSyncService

router = APIRouter()


def get_git_sync_service(
    vault_id: uuid.UUID, db: Db, _access: VaultAccess
) -> GitSyncService:
    config_repo = GitSyncConfigRepository(session=db, vault_id=vault_id)
    mapping_repo = GitSyncMappingRepository(session=db, vault_id=vault_id)
    return GitSyncService(config_repo=config_repo, mapping_repo=mapping_repo)


GitSvc = Annotated[GitSyncService, Depends(get_git_sync_service)]


@router.post("", response_model=GitSyncConfigRead, status_code=201)
async def create_config(
    body: GitSyncConfigCreate, svc: GitSvc,
) -> GitSyncConfigRead:
    config = await svc.create_config(body)
    return GitSyncConfigRead.model_validate(config)


@router.get("", response_model=GitSyncConfigRead)
async def get_config(svc: GitSvc) -> GitSyncConfigRead:
    config = await svc.get_config()
    return GitSyncConfigRead.model_validate(config)


@router.patch("", response_model=GitSyncConfigRead)
async def update_config(
    body: GitSyncConfigUpdate, svc: GitSvc,
) -> GitSyncConfigRead:
    config = await svc.update_config(body)
    return GitSyncConfigRead.model_validate(config)


@router.delete("", status_code=204)
async def delete_config(svc: GitSvc) -> None:
    await svc.delete_config()


@router.post("/sync", status_code=202)
async def trigger_sync(svc: GitSvc) -> dict[str, str]:
    await svc.trigger_sync()
    return {"status": "queued"}


@router.get("/status", response_model=GitSyncStatusRead)
async def get_status(svc: GitSvc) -> dict[str, Any]:
    return await svc.get_status()


@router.get("/mappings", response_model=list[GitSyncMappingRead])
async def list_mappings(
    svc: GitSvc,
) -> list[GitSyncMappingRead]:
    mappings = await svc.list_mappings()
    return [GitSyncMappingRead.model_validate(m) for m in mappings]


@router.post("/test-connection")
async def test_connection(svc: GitSvc) -> dict[str, Any]:
    return await svc.test_connection()
