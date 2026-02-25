import pytest
from httpx import AsyncClient

from clara.auth.models import Vault

from conftest import create_contact

pytestmark = pytest.mark.asyncio


async def test_contact_methods_crud(
    authenticated_client: AsyncClient, vault: Vault
):
    contact_id = await create_contact(authenticated_client, str(vault.id))
    base = f"/api/v1/vaults/{vault.id}/contacts/{contact_id}/methods"

    # Create
    resp = await authenticated_client.post(
        base, json={"type": "phone", "value": "+1234567890"}
    )
    assert resp.status_code == 201
    method_id = resp.json()["id"]

    # List
    resp = await authenticated_client.get(base)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

    # Update
    resp = await authenticated_client.patch(
        f"{base}/{method_id}", json={"label": "Mobile"}
    )
    assert resp.status_code == 200
    assert resp.json()["label"] == "Mobile"

    # Delete
    resp = await authenticated_client.delete(f"{base}/{method_id}")
    assert resp.status_code == 204


async def test_addresses_crud(authenticated_client: AsyncClient, vault: Vault):
    contact_id = await create_contact(authenticated_client, str(vault.id))
    base = f"/api/v1/vaults/{vault.id}/contacts/{contact_id}/addresses"

    # Create
    resp = await authenticated_client.post(
        base,
        json={"line1": "123 Main St", "city": "NYC", "postal_code": "10001", "country": "US"},
    )
    assert resp.status_code == 201
    addr_id = resp.json()["id"]

    # List
    resp = await authenticated_client.get(base)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

    # Update
    resp = await authenticated_client.patch(
        f"{base}/{addr_id}", json={"city": "Brooklyn"}
    )
    assert resp.status_code == 200
    assert resp.json()["city"] == "Brooklyn"

    # Delete
    resp = await authenticated_client.delete(f"{base}/{addr_id}")
    assert resp.status_code == 204


async def test_pets_crud(authenticated_client: AsyncClient, vault: Vault):
    contact_id = await create_contact(authenticated_client, str(vault.id))
    base = f"/api/v1/vaults/{vault.id}/contacts/{contact_id}/pets"

    # Create
    resp = await authenticated_client.post(
        base, json={"name": "Buddy", "species": "dog"}
    )
    assert resp.status_code == 201
    pet_id = resp.json()["id"]

    # List
    resp = await authenticated_client.get(base)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

    # Update
    resp = await authenticated_client.patch(
        f"{base}/{pet_id}", json={"name": "Max"}
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Max"

    # Delete
    resp = await authenticated_client.delete(f"{base}/{pet_id}")
    assert resp.status_code == 204


async def test_tags_attach_detach(authenticated_client: AsyncClient, vault: Vault):
    contact_id = await create_contact(authenticated_client, str(vault.id))

    # Create vault tag
    resp = await authenticated_client.post(
        f"/api/v1/vaults/{vault.id}/tags",
        json={"name": "VIP"},
    )
    assert resp.status_code == 201
    tag_id = resp.json()["id"]

    base = f"/api/v1/vaults/{vault.id}/contacts/{contact_id}/tags"

    # Attach
    resp = await authenticated_client.post(base, json={"tag_id": tag_id})
    assert resp.status_code == 201

    # List
    resp = await authenticated_client.get(base)
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    # Detach
    resp = await authenticated_client.delete(f"{base}/{tag_id}")
    assert resp.status_code == 204

    # Verify detached
    resp = await authenticated_client.get(base)
    assert resp.status_code == 200
    assert len(resp.json()) == 0


async def test_relationships_crud(authenticated_client: AsyncClient, vault: Vault):
    contact_a = await create_contact(authenticated_client, str(vault.id), "Alice")
    contact_b = await create_contact(authenticated_client, str(vault.id), "Bob")

    # Create relationship type
    resp = await authenticated_client.post(
        f"/api/v1/vaults/{vault.id}/relationship-types",
        json={"name": "Parent"},
    )
    assert resp.status_code == 201
    type_id = resp.json()["id"]

    base = f"/api/v1/vaults/{vault.id}/contacts/{contact_a}/relationships"

    # Create relationship
    resp = await authenticated_client.post(
        base,
        json={"other_contact_id": contact_b, "relationship_type_id": type_id},
    )
    assert resp.status_code == 201
    rel_id = resp.json()["id"]

    # List
    resp = await authenticated_client.get(base)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

    # Delete
    resp = await authenticated_client.delete(f"{base}/{rel_id}")
    assert resp.status_code == 204
