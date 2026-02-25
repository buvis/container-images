import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from clara.contacts.repository import RelationshipTypeRepository
from clara.contacts.sub_schemas import (
    RelationshipTypeCreate,
    RelationshipTypeRead,
    RelationshipTypeUpdate,
)
from clara.deps import Db, VaultAccess
from clara.exceptions import NotFoundError

router = APIRouter()


def get_repo(
    vault_id: uuid.UUID, db: Db, _access: VaultAccess
) -> RelationshipTypeRepository:
    return RelationshipTypeRepository(session=db, vault_id=vault_id)


Repo = Annotated[RelationshipTypeRepository, Depends(get_repo)]


@router.get("", response_model=list[RelationshipTypeRead])
async def list_relationship_types(repo: Repo) -> list[RelationshipTypeRead]:
    items = await repo.list_all()
    return [RelationshipTypeRead.model_validate(item) for item in items]


@router.post("", response_model=RelationshipTypeRead, status_code=201)
async def create_relationship_type(
    body: RelationshipTypeCreate, repo: Repo
) -> RelationshipTypeRead:
    item = await repo.create(**body.model_dump())
    return RelationshipTypeRead.model_validate(item)


@router.get("/{type_id}", response_model=RelationshipTypeRead)
async def get_relationship_type(type_id: uuid.UUID, repo: Repo) -> RelationshipTypeRead:
    item = await repo.get_by_id(type_id)
    if item is None:
        raise NotFoundError("RelationshipType", type_id)
    return RelationshipTypeRead.model_validate(item)


@router.patch("/{type_id}", response_model=RelationshipTypeRead)
async def update_relationship_type(
    type_id: uuid.UUID, body: RelationshipTypeUpdate, repo: Repo
) -> RelationshipTypeRead:
    item = await repo.get_by_id(type_id)
    if item is None:
        raise NotFoundError("RelationshipType", type_id)
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    await repo.session.flush()
    await repo.session.refresh(item)
    return RelationshipTypeRead.model_validate(item)


@router.delete("/{type_id}", status_code=204)
async def delete_relationship_type(type_id: uuid.UUID, repo: Repo) -> None:
    await repo.soft_delete(type_id)
