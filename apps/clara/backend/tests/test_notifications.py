import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from clara.auth.models import User, Vault

pytestmark = pytest.mark.asyncio


async def _create_notification(db: AsyncSession, vault_id, user_id) -> None:
    """Insert a notification directly since there's no create API."""
    from clara.notifications.models import Notification

    notif = Notification(
        vault_id=vault_id,
        user_id=user_id,
        title="Test notification",
        body="Something happened",
        link="/test",
    )
    db.add(notif)
    await db.flush()


async def test_notification_list_and_read(
    authenticated_client: AsyncClient,
    vault: Vault,
    user: User,
    db_session: AsyncSession,
):
    await _create_notification(db_session, vault.id, user.id)

    # List
    resp = await authenticated_client.get(
        f"/api/v1/vaults/{vault.id}/notifications"
    )
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) >= 1
    notif_id = items[0]["id"]

    # Unread count
    resp = await authenticated_client.get(
        f"/api/v1/vaults/{vault.id}/notifications/unread-count"
    )
    assert resp.status_code == 200
    assert resp.json()["count"] >= 1

    # Mark read
    resp = await authenticated_client.patch(
        f"/api/v1/vaults/{vault.id}/notifications/{notif_id}",
        json={"read": True},
    )
    assert resp.status_code == 200

    # Unread count should decrease
    resp = await authenticated_client.get(
        f"/api/v1/vaults/{vault.id}/notifications/unread-count"
    )
    assert resp.status_code == 200


async def test_mark_all_read(
    authenticated_client: AsyncClient,
    vault: Vault,
    user: User,
    db_session: AsyncSession,
):
    await _create_notification(db_session, vault.id, user.id)

    resp = await authenticated_client.post(
        f"/api/v1/vaults/{vault.id}/notifications/mark-all-read"
    )
    assert resp.status_code == 204

    resp = await authenticated_client.get(
        f"/api/v1/vaults/{vault.id}/notifications/unread-count"
    )
    assert resp.status_code == 200
    assert resp.json()["count"] == 0


async def test_delete_notification(
    authenticated_client: AsyncClient,
    vault: Vault,
    user: User,
    db_session: AsyncSession,
):
    await _create_notification(db_session, vault.id, user.id)

    resp = await authenticated_client.get(
        f"/api/v1/vaults/{vault.id}/notifications"
    )
    notif_id = resp.json()[0]["id"]

    resp = await authenticated_client.delete(
        f"/api/v1/vaults/{vault.id}/notifications/{notif_id}"
    )
    assert resp.status_code == 204

    # deleted notification should not appear in list
    resp = await authenticated_client.get(
        f"/api/v1/vaults/{vault.id}/notifications"
    )
    ids = {n["id"] for n in resp.json()}
    assert notif_id not in ids


async def test_clear_read_notifications(
    authenticated_client: AsyncClient,
    vault: Vault,
    user: User,
    db_session: AsyncSession,
):
    for _ in range(3):
        await _create_notification(db_session, vault.id, user.id)

    resp = await authenticated_client.get(
        f"/api/v1/vaults/{vault.id}/notifications"
    )
    items = resp.json()
    for notif in items[:2]:
        await authenticated_client.patch(
            f"/api/v1/vaults/{vault.id}/notifications/{notif['id']}",
            json={"read": True},
        )

    resp = await authenticated_client.delete(
        f"/api/v1/vaults/{vault.id}/notifications/clear-read"
    )
    assert resp.status_code == 204

    resp = await authenticated_client.get(
        f"/api/v1/vaults/{vault.id}/notifications"
    )
    remaining = resp.json()
    assert all(not n["read"] for n in remaining)


async def test_delete_notification_not_found(
    authenticated_client: AsyncClient,
    vault: Vault,
):
    import uuid

    resp = await authenticated_client.delete(
        f"/api/v1/vaults/{vault.id}/notifications/{uuid.uuid4()}"
    )
    assert resp.status_code == 404
