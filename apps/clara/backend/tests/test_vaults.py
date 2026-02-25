import pytest
from httpx import AsyncClient

from clara.auth.models import Vault

pytestmark = pytest.mark.asyncio


async def test_rename_vault(authenticated_client: AsyncClient, vault: Vault):
    resp = await authenticated_client.patch(
        f"/api/v1/vaults/{vault.id}",
        json={"name": "Renamed Vault"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Renamed Vault"
