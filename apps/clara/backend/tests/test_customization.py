import pytest
from httpx import AsyncClient

from clara.auth.models import Vault

pytestmark = pytest.mark.asyncio


async def test_template_crud(authenticated_client: AsyncClient, vault: Vault):
    # Create
    resp = await authenticated_client.post(
        f"/api/v1/vaults/{vault.id}/templates",
        json={"name": "Standard Contact"},
    )
    assert resp.status_code == 201
    template_id = resp.json()["id"]

    # List
    resp = await authenticated_client.get(
        f"/api/v1/vaults/{vault.id}/templates"
    )
    assert resp.status_code == 200
    assert resp.json()["meta"]["total"] >= 1

    # Get
    resp = await authenticated_client.get(
        f"/api/v1/vaults/{vault.id}/templates/{template_id}"
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Standard Contact"

    # Update
    resp = await authenticated_client.patch(
        f"/api/v1/vaults/{vault.id}/templates/{template_id}",
        json={"name": "Updated Template"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated Template"

    # Delete
    resp = await authenticated_client.delete(
        f"/api/v1/vaults/{vault.id}/templates/{template_id}"
    )
    assert resp.status_code == 204


async def test_custom_field_definition_crud(
    authenticated_client: AsyncClient, vault: Vault
):
    # Create
    resp = await authenticated_client.post(
        f"/api/v1/vaults/{vault.id}/custom-fields/definitions",
        json={
            "scope": "contact",
            "name": "Favorite Color",
            "slug": "favorite_color",
            "data_type": "text",
        },
    )
    assert resp.status_code == 201
    def_id = resp.json()["id"]

    # List
    resp = await authenticated_client.get(
        f"/api/v1/vaults/{vault.id}/custom-fields/definitions"
    )
    assert resp.status_code == 200
    assert resp.json()["meta"]["total"] >= 1

    # Get
    resp = await authenticated_client.get(
        f"/api/v1/vaults/{vault.id}/custom-fields/definitions/{def_id}"
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Favorite Color"

    # Update
    resp = await authenticated_client.patch(
        f"/api/v1/vaults/{vault.id}/custom-fields/definitions/{def_id}",
        json={"name": "Fav Color"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Fav Color"

    # Delete
    resp = await authenticated_client.delete(
        f"/api/v1/vaults/{vault.id}/custom-fields/definitions/{def_id}"
    )
    assert resp.status_code == 204
