import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from clara.base.schema import PaginatedResponse, PaginationMeta
from clara.customization.repository import (
    CustomFieldDefinitionRepository,
    CustomFieldValueRepository,
)
from clara.customization.schemas import (
    CustomFieldDefinitionCreate,
    CustomFieldDefinitionRead,
    CustomFieldDefinitionUpdate,
    CustomFieldValueRead,
    CustomFieldValueSet,
)
from clara.customization.service import CustomFieldService
from clara.deps import Db, VaultAccess
from clara.pagination import PaginationParams

router = APIRouter()


def get_custom_field_service(
    vault_id: uuid.UUID, db: Db, _access: VaultAccess
) -> CustomFieldService:
    def_repo = CustomFieldDefinitionRepository(
        session=db, vault_id=vault_id
    )
    val_repo = CustomFieldValueRepository(session=db, vault_id=vault_id)
    return CustomFieldService(def_repo=def_repo, val_repo=val_repo)


CfSvc = Annotated[CustomFieldService, Depends(get_custom_field_service)]


@router.get(
    "/definitions",
    response_model=PaginatedResponse[CustomFieldDefinitionRead],
)
async def list_definitions(
    svc: CfSvc,
    scope: str | None = Query(None),
    pagination: PaginationParams = Depends(),
) -> PaginatedResponse[CustomFieldDefinitionRead]:
    items, total = await svc.list_definitions(
        scope=scope, offset=pagination.offset, limit=pagination.limit
    )
    return PaginatedResponse(
        items=[CustomFieldDefinitionRead.model_validate(d) for d in items],
        meta=PaginationMeta(
            total=total, offset=pagination.offset, limit=pagination.limit
        ),
    )


@router.post(
    "/definitions",
    response_model=CustomFieldDefinitionRead,
    status_code=201,
)
async def create_definition(
    body: CustomFieldDefinitionCreate, svc: CfSvc
) -> CustomFieldDefinitionRead:
    return CustomFieldDefinitionRead.model_validate(
        await svc.create_definition(body)
    )


@router.get(
    "/definitions/{definition_id}",
    response_model=CustomFieldDefinitionRead,
)
async def get_definition(
    definition_id: uuid.UUID, svc: CfSvc
) -> CustomFieldDefinitionRead:
    return CustomFieldDefinitionRead.model_validate(
        await svc.get_definition(definition_id)
    )


@router.patch(
    "/definitions/{definition_id}",
    response_model=CustomFieldDefinitionRead,
)
async def update_definition(
    definition_id: uuid.UUID,
    body: CustomFieldDefinitionUpdate,
    svc: CfSvc,
) -> CustomFieldDefinitionRead:
    return CustomFieldDefinitionRead.model_validate(
        await svc.update_definition(definition_id, body)
    )


@router.delete("/definitions/{definition_id}", status_code=204)
async def delete_definition(definition_id: uuid.UUID, svc: CfSvc) -> None:
    await svc.delete_definition(definition_id)


@router.get(
    "/values/{entity_type}/{entity_id}",
    response_model=list[CustomFieldValueRead],
)
async def get_values_for_entity(
    entity_type: str, entity_id: uuid.UUID, svc: CfSvc
) -> list[CustomFieldValueRead]:
    return [
        CustomFieldValueRead.model_validate(v)
        for v in await svc.get_values_for_entity(entity_type, entity_id)
    ]


@router.put("/values", response_model=CustomFieldValueRead)
async def set_value(body: CustomFieldValueSet, svc: CfSvc) -> CustomFieldValueRead:
    return CustomFieldValueRead.model_validate(await svc.set_value(body))


@router.delete("/values/{value_id}", status_code=204)
async def delete_value(value_id: uuid.UUID, svc: CfSvc) -> None:
    await svc.delete_value(value_id)
