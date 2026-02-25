import csv
import io
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from clara.contacts.repository import ContactRepository
from clara.integrations.csv_io import export_csv, import_csv


async def test_export_csv(db_session: AsyncSession):
    vault_id = uuid.uuid4()
    repo = ContactRepository(session=db_session, vault_id=vault_id)
    await repo.create(first_name="Alice", last_name="Smith", nickname="Ali")
    await repo.create(first_name="Bob", last_name="Jones")

    result = await export_csv(db_session, vault_id)

    reader = csv.DictReader(io.StringIO(result))
    rows = list(reader)
    assert set(reader.fieldnames or []) == {
        "first_name", "last_name", "nickname", "birthdate",
        "gender", "pronouns", "favorite",
    }
    assert len(rows) == 2
    names = {r["first_name"] for r in rows}
    assert names == {"Alice", "Bob"}


async def test_import_csv(db_session: AsyncSession):
    vault_id = uuid.uuid4()
    csv_data = "first_name,last_name,nickname\nAlice,Smith,Ali\nBob,Jones,\n"

    created, errors = await import_csv(db_session, vault_id, csv_data)

    assert len(created) == 2
    assert created[0].first_name == "Alice"
    assert created[0].last_name == "Smith"
    assert created[1].first_name == "Bob"


async def test_import_csv_skips_missing_first_name(db_session: AsyncSession):
    vault_id = uuid.uuid4()
    csv_data = "first_name,last_name\n,Smith\nBob,Jones\n"

    created, errors = await import_csv(db_session, vault_id, csv_data)

    assert len(created) == 1
    assert created[0].first_name == "Bob"


async def test_roundtrip(db_session: AsyncSession):
    vault_id = uuid.uuid4()
    repo = ContactRepository(session=db_session, vault_id=vault_id)
    await repo.create(first_name="Alice", last_name="Smith", gender="female")
    await repo.create(first_name="Bob", last_name="Jones", pronouns="he/him")

    exported = await export_csv(db_session, vault_id)

    vault_id2 = uuid.uuid4()
    imported, errors = await import_csv(db_session, vault_id2, exported)

    assert len(imported) == 2
    imported_names = {(c.first_name, c.last_name) for c in imported}
    assert ("Alice", "Smith") in imported_names
    assert ("Bob", "Jones") in imported_names
