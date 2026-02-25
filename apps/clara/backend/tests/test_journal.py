import pytest
from httpx import AsyncClient

from clara.auth.models import Vault

pytestmark = pytest.mark.asyncio


async def test_journal_entry_crud(authenticated_client: AsyncClient, vault: Vault):
    # Create
    resp = await authenticated_client.post(
        f"/api/v1/vaults/{vault.id}/journal",
        json={"entry_date": "2026-02-18", "title": "Good day", "body_markdown": "Felt great", "mood": 4},
    )
    assert resp.status_code == 201
    entry_id = resp.json()["id"]

    # List
    resp = await authenticated_client.get(f"/api/v1/vaults/{vault.id}/journal")
    assert resp.status_code == 200
    assert resp.json()["meta"]["total"] >= 1

    # Get
    resp = await authenticated_client.get(
        f"/api/v1/vaults/{vault.id}/journal/{entry_id}"
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Good day"
    assert resp.json()["mood"] == 4

    # Update
    resp = await authenticated_client.patch(
        f"/api/v1/vaults/{vault.id}/journal/{entry_id}",
        json={"mood": 5},
    )
    assert resp.status_code == 200
    assert resp.json()["mood"] == 5

    # Delete
    resp = await authenticated_client.delete(
        f"/api/v1/vaults/{vault.id}/journal/{entry_id}"
    )
    assert resp.status_code == 204

    # Verify gone
    resp = await authenticated_client.get(f"/api/v1/vaults/{vault.id}/journal")
    ids = {item["id"] for item in resp.json()["items"]}
    assert entry_id not in ids


async def test_journal_pagination(authenticated_client: AsyncClient, vault: Vault):
    for i in range(3):
        resp = await authenticated_client.post(
            f"/api/v1/vaults/{vault.id}/journal",
            json={"entry_date": f"2026-01-{10 + i:02d}", "title": f"Entry {i}", "body_markdown": "content"},
        )
        assert resp.status_code == 201

    resp = await authenticated_client.get(
        f"/api/v1/vaults/{vault.id}/journal?offset=0&limit=2"
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["total"] == 3
    assert len(body["items"]) == 2
