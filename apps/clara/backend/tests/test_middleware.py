import pytest
from httpx import AsyncClient

from clara.auth.models import User, Vault
from clara.middleware import generate_csrf_token

pytestmark = pytest.mark.asyncio


@pytest.fixture()
async def cookie_client(client: AsyncClient, user: User, vault: Vault) -> AsyncClient:
    from clara.auth.security import create_access_token

    token = create_access_token(str(user.id))
    client.cookies.set("access_token", token)
    return client


async def test_mutating_with_cookie_no_csrf_rejected(
    cookie_client: AsyncClient, vault: Vault
):
    for method, url in [
        ("POST", f"/api/v1/vaults/{vault.id}/contacts"),
        ("PATCH", f"/api/v1/vaults/{vault.id}/contacts/00000000-0000-0000-0000-000000000000"),
        ("DELETE", f"/api/v1/vaults/{vault.id}/contacts/00000000-0000-0000-0000-000000000000"),
    ]:
        resp = await cookie_client.request(method, url)
        assert resp.status_code == 403, f"{method} should be rejected without CSRF"
        assert "CSRF" in resp.json()["detail"]


async def test_mutating_with_cookie_and_csrf_allowed(
    cookie_client: AsyncClient, vault: Vault
):
    access_token = cookie_client.cookies.get("access_token", "")
    csrf_token = generate_csrf_token(access_token)
    cookie_client.cookies.set("csrf_token", csrf_token)
    cookie_client.headers["x-csrf-token"] = csrf_token
    resp = await cookie_client.post(
        f"/api/v1/vaults/{vault.id}/contacts",
        json={"first_name": "Alice"},
    )
    assert resp.status_code == 201


async def test_bearer_bypasses_csrf(authenticated_client: AsyncClient, vault: Vault):
    resp = await authenticated_client.post(
        f"/api/v1/vaults/{vault.id}/contacts",
        json={"first_name": "Bob"},
    )
    assert resp.status_code == 201


async def test_safe_methods_no_csrf(cookie_client: AsyncClient, vault: Vault):
    for method in ("GET", "HEAD", "OPTIONS"):
        resp = await cookie_client.request(method, f"/api/v1/vaults/{vault.id}/contacts")
        assert resp.status_code != 403, f"{method} should not require CSRF"
