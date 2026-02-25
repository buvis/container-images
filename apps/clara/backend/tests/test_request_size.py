import pytest
from httpx import AsyncClient

from clara.auth.models import Vault

pytestmark = pytest.mark.asyncio


async def test_oversized_json_rejected(authenticated_client: AsyncClient, vault: Vault):
    """JSON request exceeding max_body_size should get 413."""
    oversized = {"first_name": "x" * 2_000_000}
    resp = await authenticated_client.post(
        f"/api/v1/vaults/{vault.id}/contacts",
        json=oversized,
    )
    assert resp.status_code == 413


async def test_normal_json_accepted(authenticated_client: AsyncClient, vault: Vault):
    """Normal-sized JSON request should pass through."""
    resp = await authenticated_client.post(
        f"/api/v1/vaults/{vault.id}/contacts",
        json={"first_name": "Alice"},
    )
    assert resp.status_code == 201
