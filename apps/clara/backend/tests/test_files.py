import pytest
from httpx import AsyncClient

from clara.auth.models import Vault

pytestmark = pytest.mark.asyncio


async def test_file_upload_and_crud(authenticated_client: AsyncClient, vault: Vault):
    # Upload
    resp = await authenticated_client.post(
        f"/api/v1/vaults/{vault.id}/files",
        files={"file": ("test.txt", b"hello world", "text/plain")},
    )
    assert resp.status_code == 201
    file_id = resp.json()["id"]
    assert resp.json()["filename"] == "test.txt"

    # List
    resp = await authenticated_client.get(f"/api/v1/vaults/{vault.id}/files")
    assert resp.status_code == 200
    assert resp.json()["meta"]["total"] >= 1

    # Get metadata
    resp = await authenticated_client.get(
        f"/api/v1/vaults/{vault.id}/files/{file_id}"
    )
    assert resp.status_code == 200
    assert resp.json()["mime_type"] == "text/plain"

    # Delete
    resp = await authenticated_client.delete(
        f"/api/v1/vaults/{vault.id}/files/{file_id}"
    )
    assert resp.status_code == 204


async def test_file_rename(authenticated_client: AsyncClient, vault: Vault):
    resp = await authenticated_client.post(
        f"/api/v1/vaults/{vault.id}/files",
        files={"file": ("original.txt", b"data", "text/plain")},
    )
    assert resp.status_code == 201
    file_id = resp.json()["id"]

    resp = await authenticated_client.patch(
        f"/api/v1/vaults/{vault.id}/files/{file_id}",
        json={"filename": "renamed.txt"},
    )
    assert resp.status_code == 200
    assert resp.json()["filename"] == "renamed.txt"
