import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_register_success(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "new-user@example.com",
            "password": "Password123!",
            "name": "New User",
        },
    )
    assert response.status_code == 201
    assert response.cookies.get("access_token") is not None
    assert response.cookies.get("refresh_token") is not None
    assert response.cookies.get("csrf_token") is not None


async def test_register_duplicate(client: AsyncClient):
    payload = {
        "email": "dupe@example.com",
        "password": "Password123!",
        "name": "Dupe",
    }
    first = await client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 201
    client.headers["x-csrf-token"] = client.cookies.get("csrf_token", "")

    second = await client.post("/api/v1/auth/register", json=payload)
    assert second.status_code == 409


async def test_register_weak_password(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "weak@example.com",
            "password": "short",
            "name": "Weak User",
        },
    )
    assert response.status_code == 422


async def test_login_success(client: AsyncClient):
    register = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "login-success@example.com",
            "password": "Password123!",
            "name": "Login Success",
        },
    )
    assert register.status_code == 201
    client.cookies.clear()

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "login-success@example.com", "password": "Password123!"},
    )
    assert response.status_code == 200
    assert response.json()["access_token"]


async def test_login_wrong_password(client: AsyncClient):
    register = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "wrong-pass@example.com",
            "password": "Password123!",
            "name": "Wrong Pass",
        },
    )
    assert register.status_code == 201
    client.cookies.clear()

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "wrong-pass@example.com", "password": "bad-password"},
    )
    assert response.status_code == 401


async def test_me_authenticated(authenticated_client: AsyncClient):
    response = await authenticated_client.get("/api/v1/auth/me")
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"


async def test_me_unauthenticated(client: AsyncClient):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


async def test_forgot_password_no_token_in_logs(
    client: AsyncClient, user, vault, caplog,
):
    """Password reset must not log token or email in application logs."""
    import logging

    with caplog.at_level(logging.INFO, logger="clara"):
        resp = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": user.email},
        )
    assert resp.status_code == 200
    app_logs = [r for r in caplog.records if r.name.startswith("clara")]
    for record in app_logs:
        msg = record.getMessage().lower()
        assert "token for" not in msg
        assert user.email.lower() not in msg


async def test_pat_read_scope_blocks_write(
    authenticated_client: AsyncClient, vault,
):
    """Read-only PAT should get 403 on POST endpoints."""
    resp = await authenticated_client.post(
        "/api/v1/auth/tokens",
        json={"name": "ro", "scopes": ["read"]},
    )
    assert resp.status_code == 201
    token = resp.json()["token"]

    # Use per-request headers to override cookies with PAT
    resp = await authenticated_client.request(
        "POST",
        f"/api/v1/vaults/{vault.id}/contacts",
        json={"first_name": "Blocked"},
        headers={
            "Authorization": f"Bearer {token}",
            "Cookie": "",  # clear cookies for this request
        },
    )
    assert resp.status_code == 403
    assert "scope" in resp.json()["detail"].lower()


async def test_pat_readwrite_scope_allows_write(
    authenticated_client: AsyncClient, vault,
):
    """Read+write PAT should succeed on POST endpoints."""
    resp = await authenticated_client.post(
        "/api/v1/auth/tokens",
        json={"name": "rw", "scopes": ["read", "write"]},
    )
    assert resp.status_code == 201
    token = resp.json()["token"]

    resp = await authenticated_client.request(
        "POST",
        f"/api/v1/vaults/{vault.id}/contacts",
        json={"first_name": "Allowed"},
        headers={
            "Authorization": f"Bearer {token}",
            "Cookie": "",
        },
    )
    assert resp.status_code == 201


async def test_register_rate_limited(client: AsyncClient):
    """Register endpoint should return 429 after 3 attempts per IP."""
    for i in range(3):
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": f"ratelimit{i}@example.com",
                "password": "Password123!",
                "name": f"Rate Limit {i}",
            },
        )
        client.cookies.clear()

    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "ratelimit-blocked@example.com",
            "password": "Password123!",
            "name": "Blocked",
        },
    )
    assert resp.status_code == 429
