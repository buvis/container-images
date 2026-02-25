import pytest
from httpx import AsyncClient

from clara.auth.models import Vault

from conftest import create_contact

pytestmark = pytest.mark.asyncio


async def test_debt_crud(authenticated_client: AsyncClient, vault: Vault):
    contact_id = await create_contact(authenticated_client, str(vault.id))

    # Create
    resp = await authenticated_client.post(
        f"/api/v1/vaults/{vault.id}/debts",
        json={
            "contact_id": contact_id,
            "direction": "owed_to_you",
            "amount": "50.00",
        },
    )
    assert resp.status_code == 201
    debt_id = resp.json()["id"]

    # List
    resp = await authenticated_client.get(f"/api/v1/vaults/{vault.id}/debts")
    assert resp.status_code == 200
    assert resp.json()["meta"]["total"] >= 1

    # Get
    resp = await authenticated_client.get(
        f"/api/v1/vaults/{vault.id}/debts/{debt_id}"
    )
    assert resp.status_code == 200

    # Update
    resp = await authenticated_client.patch(
        f"/api/v1/vaults/{vault.id}/debts/{debt_id}",
        json={"settled": True},
    )
    assert resp.status_code == 200
    assert resp.json()["settled"] is True

    # Delete
    resp = await authenticated_client.delete(
        f"/api/v1/vaults/{vault.id}/debts/{debt_id}"
    )
    assert resp.status_code == 204
