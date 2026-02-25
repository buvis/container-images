import pytest
from httpx import AsyncClient

from clara.auth.models import Vault

from conftest import create_contact

pytestmark = pytest.mark.asyncio


async def test_gift_crud(authenticated_client: AsyncClient, vault: Vault):
    contact_id = await create_contact(authenticated_client, str(vault.id))

    # Create
    resp = await authenticated_client.post(
        f"/api/v1/vaults/{vault.id}/gifts",
        json={"contact_id": contact_id, "direction": "given", "name": "Book"},
    )
    assert resp.status_code == 201
    gift_id = resp.json()["id"]

    # List
    resp = await authenticated_client.get(f"/api/v1/vaults/{vault.id}/gifts")
    assert resp.status_code == 200
    assert resp.json()["meta"]["total"] >= 1

    # Get
    resp = await authenticated_client.get(
        f"/api/v1/vaults/{vault.id}/gifts/{gift_id}"
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Book"

    # Update
    resp = await authenticated_client.patch(
        f"/api/v1/vaults/{vault.id}/gifts/{gift_id}",
        json={"name": "Novel", "status": "purchased"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Novel"

    # Delete
    resp = await authenticated_client.delete(
        f"/api/v1/vaults/{vault.id}/gifts/{gift_id}"
    )
    assert resp.status_code == 204
