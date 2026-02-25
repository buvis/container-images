import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from clara.deps import Db, VaultAccess
from clara.reminders.repository import StayInTouchRepository
from clara.reminders.schemas import StayInTouchCreateOrUpdate, StayInTouchRead
from clara.reminders.service import StayInTouchService

router = APIRouter()


def get_stay_in_touch_service(
    vault_id: uuid.UUID, db: Db, _access: VaultAccess
) -> StayInTouchService:
    repo = StayInTouchRepository(session=db, vault_id=vault_id)
    return StayInTouchService(repo=repo)


SitSvc = Annotated[StayInTouchService, Depends(get_stay_in_touch_service)]


@router.get("", response_model=StayInTouchRead | None)
async def get_stay_in_touch(
    contact_id: uuid.UUID, svc: SitSvc
) -> StayInTouchRead | None:
    config = await svc.get_config(contact_id)
    if config is None:
        return None
    return StayInTouchRead.model_validate(config)


@router.put("", response_model=StayInTouchRead)
async def set_stay_in_touch(
    contact_id: uuid.UUID,
    body: StayInTouchCreateOrUpdate,
    svc: SitSvc,
) -> StayInTouchRead:
    config = await svc.set_config(contact_id, body)
    return StayInTouchRead.model_validate(config)


@router.delete("", status_code=204)
async def delete_stay_in_touch(contact_id: uuid.UUID, svc: SitSvc) -> None:
    await svc.delete_config(contact_id)
