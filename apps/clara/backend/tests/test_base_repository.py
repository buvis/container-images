import uuid

import pytest
from sqlalchemy import String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from clara.base.model import VaultScopedModel
from clara.base.repository import BaseRepository
from clara.exceptions import NotFoundError


class FakeModel(VaultScopedModel):
    __tablename__ = "fake_for_test"
    name: Mapped[str] = mapped_column(String(255))


class FakeRepo(BaseRepository[FakeModel]):
    model = FakeModel


def test_repo_has_model():
    assert FakeRepo.model is FakeModel


async def test_create(db_session: AsyncSession):
    vault_id = uuid.uuid4()
    repo = FakeRepo(db_session, vault_id)

    obj = await repo.create(name="Alice")

    assert obj.id is not None
    assert obj.name == "Alice"
    assert obj.vault_id == vault_id
    assert obj.deleted_at is None


async def test_get_by_id(db_session: AsyncSession):
    vault_id = uuid.uuid4()
    repo = FakeRepo(db_session, vault_id)
    created = await repo.create(name="Bob")

    fetched = await repo.get_by_id(created.id)

    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.name == "Bob"


async def test_get_by_id_not_found(db_session: AsyncSession):
    repo = FakeRepo(db_session, uuid.uuid4())

    result = await repo.get_by_id(uuid.uuid4())

    assert result is None


async def test_list(db_session: AsyncSession):
    vault_id = uuid.uuid4()
    repo = FakeRepo(db_session, vault_id)
    await repo.create(name="A")
    await repo.create(name="B")
    await repo.create(name="C")

    items, total = await repo.list()

    assert total == 3
    assert len(items) == 3


async def test_list_pagination(db_session: AsyncSession):
    vault_id = uuid.uuid4()
    repo = FakeRepo(db_session, vault_id)
    for i in range(5):
        await repo.create(name=f"Item {i}")

    page1, total = await repo.list(offset=0, limit=2)
    assert total == 5
    assert len(page1) == 2

    page2, _ = await repo.list(offset=2, limit=2)
    assert len(page2) == 2

    page3, _ = await repo.list(offset=4, limit=2)
    assert len(page3) == 1

    all_ids = {o.id for o in page1} | {o.id for o in page2} | {o.id for o in page3}
    assert len(all_ids) == 5


async def test_update(db_session: AsyncSession):
    vault_id = uuid.uuid4()
    repo = FakeRepo(db_session, vault_id)
    created = await repo.create(name="Original")

    updated = await repo.update(created.id, name="Changed")

    assert updated.id == created.id
    assert updated.name == "Changed"


async def test_update_not_found(db_session: AsyncSession):
    repo = FakeRepo(db_session, uuid.uuid4())
    missing_id = uuid.uuid4()

    with pytest.raises(NotFoundError) as exc_info:
        await repo.update(missing_id, name="X")

    assert exc_info.value.id == missing_id


async def test_soft_delete(db_session: AsyncSession):
    vault_id = uuid.uuid4()
    repo = FakeRepo(db_session, vault_id)
    created = await repo.create(name="ToDelete")

    await repo.soft_delete(created.id)

    # excluded from get_by_id
    assert await repo.get_by_id(created.id) is None

    # excluded from list
    items, total = await repo.list()
    assert total == 0
    assert len(items) == 0


async def test_soft_delete_not_found(db_session: AsyncSession):
    repo = FakeRepo(db_session, uuid.uuid4())
    missing_id = uuid.uuid4()

    with pytest.raises(NotFoundError) as exc_info:
        await repo.soft_delete(missing_id)

    assert exc_info.value.id == missing_id


async def test_vault_scoping(db_session: AsyncSession):
    vault_a = uuid.uuid4()
    vault_b = uuid.uuid4()
    repo_a = FakeRepo(db_session, vault_a)
    repo_b = FakeRepo(db_session, vault_b)

    obj_a = await repo_a.create(name="Vault A item")
    await repo_b.create(name="Vault B item")

    # repo_b can't see repo_a's entity
    assert await repo_b.get_by_id(obj_a.id) is None

    # each vault lists only its own
    items_a, total_a = await repo_a.list()
    items_b, total_b = await repo_b.list()
    assert total_a == 1
    assert total_b == 1
    assert items_a[0].name == "Vault A item"
    assert items_b[0].name == "Vault B item"


async def test_filtered_list(db_session: AsyncSession):
    vault_id = uuid.uuid4()
    repo = FakeRepo(db_session, vault_id)
    await repo.create(name="apple")
    await repo.create(name="apricot")
    await repo.create(name="banana")

    items, total = await repo.filtered_list(
        FakeModel.name.like("ap%"),
    )

    assert total == 2
    assert {i.name for i in items} == {"apple", "apricot"}
