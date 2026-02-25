import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from clara.activities.repository import (
    ActivityParticipantRepository,
    ActivityRepository,
    ActivityTypeRepository,
)
from clara.activities.schemas import (
    ActivityCreate,
    ActivityRead,
    ActivityTypeCreate,
    ActivityTypeRead,
    ActivityTypeUpdate,
    ActivityUpdate,
    ParticipantInput,
    ParticipantRead,
)
from clara.activities.service import ActivityService, ActivityTypeService
from clara.base.schema import PaginatedResponse, PaginationMeta
from clara.deps import Db, VaultAccess
from clara.pagination import PaginationParams

router = APIRouter()


# --- dependency factories ---


def get_activity_type_service(
    vault_id: uuid.UUID, db: Db, _access: VaultAccess
) -> ActivityTypeService:
    repo = ActivityTypeRepository(session=db, vault_id=vault_id)
    return ActivityTypeService(repo=repo)


def get_activity_service(
    vault_id: uuid.UUID, db: Db, _access: VaultAccess
) -> ActivityService:
    repo = ActivityRepository(session=db, vault_id=vault_id)
    participant_repo = ActivityParticipantRepository(
        session=db, vault_id=vault_id
    )
    return ActivityService(repo=repo, participant_repo=participant_repo)


TypeSvc = Annotated[ActivityTypeService, Depends(get_activity_type_service)]
ActivitySvc = Annotated[ActivityService, Depends(get_activity_service)]


# --- activity type endpoints ---


@router.get("/types", response_model=PaginatedResponse[ActivityTypeRead])
async def list_activity_types(
    svc: TypeSvc, pagination: PaginationParams = Depends()
) -> PaginatedResponse[ActivityTypeRead]:
    items, total = await svc.list_types(
        offset=pagination.offset, limit=pagination.limit
    )
    return PaginatedResponse(
        items=[ActivityTypeRead.model_validate(t) for t in items],
        meta=PaginationMeta(
            total=total, offset=pagination.offset, limit=pagination.limit
        ),
    )


@router.post("/types", response_model=ActivityTypeRead, status_code=201)
async def create_activity_type(
    body: ActivityTypeCreate, svc: TypeSvc
) -> ActivityTypeRead:
    return ActivityTypeRead.model_validate(await svc.create_type(body))


@router.patch("/types/{type_id}", response_model=ActivityTypeRead)
async def update_activity_type(
    type_id: uuid.UUID, body: ActivityTypeUpdate, svc: TypeSvc
) -> ActivityTypeRead:
    return ActivityTypeRead.model_validate(await svc.update_type(type_id, body))


@router.delete("/types/{type_id}", status_code=204)
async def delete_activity_type(type_id: uuid.UUID, svc: TypeSvc) -> None:
    await svc.delete_type(type_id)


# --- activity endpoints ---


@router.get("", response_model=PaginatedResponse[ActivityRead])
async def list_activities(
    svc: ActivitySvc,
    pagination: PaginationParams = Depends(),
    q: str | None = None,
) -> PaginatedResponse[ActivityRead]:
    items, total = await svc.list_activities(
        offset=pagination.offset, limit=pagination.limit, q=q
    )
    return PaginatedResponse(
        items=[ActivityRead.model_validate(a) for a in items],
        meta=PaginationMeta(
            total=total, offset=pagination.offset, limit=pagination.limit
        ),
    )


@router.get("/{activity_id}", response_model=ActivityRead)
async def get_activity(activity_id: uuid.UUID, svc: ActivitySvc) -> ActivityRead:
    return ActivityRead.model_validate(await svc.get_activity(activity_id))


@router.post("", response_model=ActivityRead, status_code=201)
async def create_activity(body: ActivityCreate, svc: ActivitySvc) -> ActivityRead:
    return ActivityRead.model_validate(await svc.create_activity(body))


@router.patch("/{activity_id}", response_model=ActivityRead)
async def update_activity(
    activity_id: uuid.UUID, body: ActivityUpdate, svc: ActivitySvc
) -> ActivityRead:
    return ActivityRead.model_validate(
        await svc.update_activity(activity_id, body)
    )


@router.delete("/{activity_id}", status_code=204)
async def delete_activity(activity_id: uuid.UUID, svc: ActivitySvc) -> None:
    await svc.delete_activity(activity_id)


# --- participant management on an activity ---


@router.post(
    "/{activity_id}/participants",
    response_model=ParticipantRead,
    status_code=201,
)
async def add_participant(
    activity_id: uuid.UUID, body: ParticipantInput, svc: ActivitySvc
) -> ParticipantRead:
    await svc.add_participant(
        activity_id, body.contact_id, body.role
    )
    activity = await svc.get_activity(activity_id)
    return next(
        ParticipantRead.model_validate(p)
        for p in activity.participants
        if p.contact_id == body.contact_id
    )


@router.delete(
    "/{activity_id}/participants/{participant_id}", status_code=204
)
async def remove_participant(
    activity_id: uuid.UUID,
    participant_id: uuid.UUID,
    svc: ActivitySvc,
) -> None:
    await svc.remove_participant(participant_id)
