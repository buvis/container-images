import pytest
from httpx import AsyncClient

from clara.auth.models import Vault

pytestmark = pytest.mark.asyncio


async def test_create_contact(authenticated_client: AsyncClient, vault: Vault):
    response = await authenticated_client.post(
        f"/api/v1/vaults/{vault.id}/contacts",
        json={"first_name": "Alice", "last_name": "Smith"},
    )
    assert response.status_code == 201
    assert response.json()["first_name"] == "Alice"


async def test_list_contacts(authenticated_client: AsyncClient, vault: Vault):
    create = await authenticated_client.post(
        f"/api/v1/vaults/{vault.id}/contacts",
        json={"first_name": "Bob"},
    )
    assert create.status_code == 201

    response = await authenticated_client.get(
        f"/api/v1/vaults/{vault.id}/contacts?offset=0&limit=10"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["total"] == 1
    assert len(body["items"]) == 1


async def test_get_contact(authenticated_client: AsyncClient, vault: Vault):
    create = await authenticated_client.post(
        f"/api/v1/vaults/{vault.id}/contacts",
        json={"first_name": "Charlie"},
    )
    assert create.status_code == 201
    contact_id = create.json()["id"]

    response = await authenticated_client.get(
        f"/api/v1/vaults/{vault.id}/contacts/{contact_id}"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == contact_id
    assert "relationships" in data
    assert data["relationships"] == []


async def test_update_contact(authenticated_client: AsyncClient, vault: Vault):
    create = await authenticated_client.post(
        f"/api/v1/vaults/{vault.id}/contacts",
        json={"first_name": "Dani"},
    )
    assert create.status_code == 201
    contact_id = create.json()["id"]

    response = await authenticated_client.patch(
        f"/api/v1/vaults/{vault.id}/contacts/{contact_id}",
        json={"first_name": "Danielle", "favorite": True},
    )
    assert response.status_code == 200
    assert response.json()["first_name"] == "Danielle"
    assert response.json()["favorite"] is True


async def test_delete_contact(authenticated_client: AsyncClient, vault: Vault):
    create = await authenticated_client.post(
        f"/api/v1/vaults/{vault.id}/contacts",
        json={"first_name": "Eli"},
    )
    assert create.status_code == 201
    contact_id = create.json()["id"]

    delete = await authenticated_client.delete(
        f"/api/v1/vaults/{vault.id}/contacts/{contact_id}"
    )
    assert delete.status_code == 204

    listed = await authenticated_client.get(f"/api/v1/vaults/{vault.id}/contacts")
    assert listed.status_code == 200
    ids = {item["id"] for item in listed.json()["items"]}
    assert contact_id not in ids


async def test_contact_count_with_multiple_tags(
    authenticated_client: AsyncClient, vault: Vault,
):
    """Filtering by multiple tags should not duplicate contacts in count."""
    # Create 2 tags
    tag1 = await authenticated_client.post(
        f"/api/v1/vaults/{vault.id}/tags", json={"name": "tag1"},
    )
    tag2 = await authenticated_client.post(
        f"/api/v1/vaults/{vault.id}/tags", json={"name": "tag2"},
    )
    assert tag1.status_code == 201
    assert tag2.status_code == 201
    tag1_id = tag1.json()["id"]
    tag2_id = tag2.json()["id"]

    # Create contact
    contact = await authenticated_client.post(
        f"/api/v1/vaults/{vault.id}/contacts", json={"first_name": "Tagged"},
    )
    assert contact.status_code == 201
    contact_id = contact.json()["id"]

    # Attach both tags
    r1 = await authenticated_client.post(
        f"/api/v1/vaults/{vault.id}/contacts/{contact_id}/tags",
        json={"tag_id": tag1_id},
    )
    r2 = await authenticated_client.post(
        f"/api/v1/vaults/{vault.id}/contacts/{contact_id}/tags",
        json={"tag_id": tag2_id},
    )
    assert r1.status_code == 201
    assert r2.status_code == 201

    # Filter by both tags — should get 1 contact, not 2
    resp = await authenticated_client.get(
        f"/api/v1/vaults/{vault.id}/contacts?tags={tag1_id},{tag2_id}"
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["total"] == 1
    assert len(body["items"]) == 1


async def test_filter_by_favorites(authenticated_client: AsyncClient, vault: Vault):
    first = await authenticated_client.post(
        f"/api/v1/vaults/{vault.id}/contacts",
        json={"first_name": "Fav", "favorite": True},
    )
    second = await authenticated_client.post(
        f"/api/v1/vaults/{vault.id}/contacts",
        json={"first_name": "NotFav", "favorite": False},
    )
    assert first.status_code == 201
    assert second.status_code == 201

    response = await authenticated_client.get(
        f"/api/v1/vaults/{vault.id}/contacts?favorites=true"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["total"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["favorite"] is True


async def test_contacts_pagination(authenticated_client: AsyncClient, vault: Vault):
    # create 3 contacts
    for name in ["Alice", "Bob", "Carol"]:
        resp = await authenticated_client.post(
            f"/api/v1/vaults/{vault.id}/contacts",
            json={"first_name": name},
        )
        assert resp.status_code == 201

    # page 1: limit=2
    resp = await authenticated_client.get(
        f"/api/v1/vaults/{vault.id}/contacts?offset=0&limit=2"
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["total"] == 3
    assert len(body["items"]) == 2

    # page 2: offset=2, limit=2
    resp = await authenticated_client.get(
        f"/api/v1/vaults/{vault.id}/contacts?offset=2&limit=2"
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["total"] == 3
    assert len(body["items"]) == 1


async def test_update_contact_photo_file_id(
    authenticated_client: AsyncClient, vault: Vault
):
    import uuid
    from conftest import create_contact

    contact_id = await create_contact(authenticated_client, str(vault.id))
    fake_file_id = str(uuid.uuid4())

    resp = await authenticated_client.patch(
        f"/api/v1/vaults/{vault.id}/contacts/{contact_id}",
        json={"photo_file_id": fake_file_id},
    )
    assert resp.status_code == 200
    assert resp.json()["photo_file_id"] == fake_file_id


async def test_contacts_sorting_by_created_at(
    authenticated_client: AsyncClient, vault: Vault
):
    """Contacts should be returned newest-first (created_at desc)."""
    for name in ["First", "Second", "Third"]:
        await authenticated_client.post(
            f"/api/v1/vaults/{vault.id}/contacts",
            json={"first_name": name},
        )

    resp = await authenticated_client.get(
        f"/api/v1/vaults/{vault.id}/contacts?offset=0&limit=10"
    )
    items = resp.json()["items"]
    dates = [item["created_at"] for item in items]
    assert dates == sorted(dates, reverse=True)
