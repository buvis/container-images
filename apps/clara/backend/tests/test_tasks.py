import pytest
from httpx import AsyncClient

from clara.auth.models import Vault

pytestmark = pytest.mark.asyncio


async def test_task_crud(authenticated_client: AsyncClient, vault: Vault):
    # Create
    resp = await authenticated_client.post(
        f"/api/v1/vaults/{vault.id}/tasks",
        json={"title": "Buy groceries"},
    )
    assert resp.status_code == 201
    task_id = resp.json()["id"]
    assert resp.json()["status"] == "pending"

    # List
    resp = await authenticated_client.get(f"/api/v1/vaults/{vault.id}/tasks")
    assert resp.status_code == 200
    assert resp.json()["meta"]["total"] >= 1

    # Get
    resp = await authenticated_client.get(
        f"/api/v1/vaults/{vault.id}/tasks/{task_id}"
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Buy groceries"

    # Update
    resp = await authenticated_client.patch(
        f"/api/v1/vaults/{vault.id}/tasks/{task_id}",
        json={"title": "Buy organic groceries", "status": "done"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "done"

    # Delete
    resp = await authenticated_client.delete(
        f"/api/v1/vaults/{vault.id}/tasks/{task_id}"
    )
    assert resp.status_code == 204

    # Verify gone
    resp = await authenticated_client.get(f"/api/v1/vaults/{vault.id}/tasks")
    ids = {item["id"] for item in resp.json()["items"]}
    assert task_id not in ids


async def test_tasks_pagination(authenticated_client: AsyncClient, vault: Vault):
    for i in range(3):
        resp = await authenticated_client.post(
            f"/api/v1/vaults/{vault.id}/tasks",
            json={"title": f"Task {i}"},
        )
        assert resp.status_code == 201

    resp = await authenticated_client.get(
        f"/api/v1/vaults/{vault.id}/tasks?offset=0&limit=2"
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["total"] == 3
    assert len(body["items"]) == 2

    resp = await authenticated_client.get(
        f"/api/v1/vaults/{vault.id}/tasks?offset=2&limit=2"
    )
    body = resp.json()
    assert body["meta"]["total"] == 3
    assert len(body["items"]) == 1
