import uuid

import pytest
from httpx import AsyncClient

from clara.auth.models import Vault

pytestmark = pytest.mark.asyncio


async def test_note_crud(authenticated_client: AsyncClient, vault: Vault):
    # Create — created_by_id required by schema (endpoint overrides it)
    resp = await authenticated_client.post(
        f"/api/v1/vaults/{vault.id}/notes",
        json={
            "title": "Meeting notes",
            "body_markdown": "# Discussion points",
            "created_by_id": str(uuid.uuid4()),
        },
    )
    assert resp.status_code == 201
    note_id = resp.json()["id"]

    # List
    resp = await authenticated_client.get(f"/api/v1/vaults/{vault.id}/notes")
    assert resp.status_code == 200
    assert resp.json()["meta"]["total"] >= 1

    # Get
    resp = await authenticated_client.get(
        f"/api/v1/vaults/{vault.id}/notes/{note_id}"
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Meeting notes"

    # Update
    resp = await authenticated_client.patch(
        f"/api/v1/vaults/{vault.id}/notes/{note_id}",
        json={"title": "Updated notes"},
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated notes"

    # Delete
    resp = await authenticated_client.delete(
        f"/api/v1/vaults/{vault.id}/notes/{note_id}"
    )
    assert resp.status_code == 204

    # Verify gone
    resp = await authenticated_client.get(f"/api/v1/vaults/{vault.id}/notes")
    ids = {item["id"] for item in resp.json()["items"]}
    assert note_id not in ids
