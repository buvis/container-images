import json
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from clara.contacts.repository import ContactRepository
from clara.integrations.json_export import export_vault_json


EXPECTED_KEYS = {
    "vault_id", "contacts", "contact_methods", "addresses",
    "contact_relationships", "tags", "pets", "activity_types",
    "activities", "activity_participants", "notes", "reminders",
    "stay_in_touch_configs", "tasks", "journal_entries",
    "journal_entry_contacts", "gifts", "debts",
}


async def test_export_json(db_session: AsyncSession):
    vault_id = uuid.uuid4()
    repo = ContactRepository(session=db_session, vault_id=vault_id)
    await repo.create(first_name="Alice", last_name="Smith")

    result = await export_vault_json(db_session, vault_id)

    assert set(result.keys()) == EXPECTED_KEYS
    assert result["vault_id"] == str(vault_id)
    # valid JSON round-trip
    serialized = json.dumps(result)
    parsed = json.loads(serialized)
    assert parsed["vault_id"] == str(vault_id)
    assert len(parsed["contacts"]) == 1
    assert parsed["contacts"][0]["first_name"] == "Alice"


async def test_export_json_empty_vault(db_session: AsyncSession):
    vault_id = uuid.uuid4()

    result = await export_vault_json(db_session, vault_id)

    assert set(result.keys()) == EXPECTED_KEYS
    for key in EXPECTED_KEYS - {"vault_id"}:
        assert result[key] == []
