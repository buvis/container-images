import uuid

import pytest
from httpx import AsyncClient

from clara.auth.models import Vault

pytestmark = pytest.mark.asyncio


# --- 404 Not Found ---


async def test_get_contact_not_found(
    authenticated_client: AsyncClient, vault: Vault
):
    resp = await authenticated_client.get(
        f"/api/v1/vaults/{vault.id}/contacts/{uuid.uuid4()}"
    )
    assert resp.status_code == 404


async def test_get_task_not_found(
    authenticated_client: AsyncClient, vault: Vault
):
    resp = await authenticated_client.get(
        f"/api/v1/vaults/{vault.id}/tasks/{uuid.uuid4()}"
    )
    assert resp.status_code == 404


async def test_delete_contact_not_found(
    authenticated_client: AsyncClient, vault: Vault
):
    resp = await authenticated_client.delete(
        f"/api/v1/vaults/{vault.id}/contacts/{uuid.uuid4()}"
    )
    assert resp.status_code == 404


async def test_patch_notification_not_found(
    authenticated_client: AsyncClient, vault: Vault
):
    resp = await authenticated_client.patch(
        f"/api/v1/vaults/{vault.id}/notifications/{uuid.uuid4()}",
        json={"read": True},
    )
    assert resp.status_code == 404


# --- 422 Validation Error ---


async def test_create_contact_empty_body(
    authenticated_client: AsyncClient, vault: Vault
):
    resp = await authenticated_client.post(
        f"/api/v1/vaults/{vault.id}/contacts",
        json={},
    )
    assert resp.status_code == 422


async def test_create_task_missing_title(
    authenticated_client: AsyncClient, vault: Vault
):
    resp = await authenticated_client.post(
        f"/api/v1/vaults/{vault.id}/tasks",
        json={},
    )
    assert resp.status_code == 422


# --- 403 Forbidden (wrong vault) ---


async def test_access_wrong_vault(
    authenticated_client: AsyncClient,
):
    """Accessing a vault the user is not a member of should return 403."""
    fake_vault = uuid.uuid4()
    resp = await authenticated_client.get(
        f"/api/v1/vaults/{fake_vault}/contacts"
    )
    assert resp.status_code == 403
