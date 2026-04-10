"""Tests for auth endpoints: login, me, invalid credentials."""

import pytest


@pytest.mark.asyncio
async def test_health(client):
    res = await client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_login_success(client, seed_user):
    res = await client.post("/api/auth/login", json={"email": "test@horarios.app", "password": "test123"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client, seed_user):
    res = await client.post("/api/auth/login", json={"email": "test@horarios.app", "password": "wrong"})
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client):
    res = await client.post("/api/auth/login", json={"email": "nobody@test.com", "password": "test"})
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_me_authenticated(auth_client, seed_user):
    res = await auth_client.get("/api/auth/me")
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "test@horarios.app"
    assert data["display_name"] == "Test User"


@pytest.mark.asyncio
async def test_me_no_token(client):
    res = await client.get("/api/auth/me")
    assert res.status_code in (401, 403)  # HTTPBearer returns 403 without header, 401 with bad token


@pytest.mark.asyncio
async def test_me_invalid_token(client):
    res = await client.get("/api/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
    assert res.status_code == 401
