"""Tests for members CRUD endpoints."""

import pytest


@pytest.mark.asyncio
async def test_create_member(auth_client):
    res = await auth_client.post("/api/members", json={
        "full_name": "Ana Garcia", "role_name": "Enfermera", "weekly_hour_limit": 40, "color_tag": "#F472B6"
    })
    assert res.status_code == 201
    data = res.json()
    assert data["full_name"] == "Ana Garcia"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_list_members(auth_client):
    await auth_client.post("/api/members", json={"full_name": "A", "role_name": "R", "weekly_hour_limit": 40, "color_tag": "#F472B6"})
    await auth_client.post("/api/members", json={"full_name": "B", "role_name": "R", "weekly_hour_limit": 35, "color_tag": "#818CF8"})
    res = await auth_client.get("/api/members")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_update_member(auth_client):
    create = await auth_client.post("/api/members", json={"full_name": "Old Name", "role_name": "R", "weekly_hour_limit": 40, "color_tag": "#F472B6"})
    mid = create.json()["id"]
    res = await auth_client.put(f"/api/members/{mid}", json={"full_name": "New Name"})
    assert res.status_code == 200
    assert res.json()["full_name"] == "New Name"


@pytest.mark.asyncio
async def test_delete_member_soft(auth_client):
    create = await auth_client.post("/api/members", json={"full_name": "To Delete", "role_name": "R", "weekly_hour_limit": 40, "color_tag": "#F472B6"})
    mid = create.json()["id"]
    res = await auth_client.delete(f"/api/members/{mid}")
    assert res.status_code == 200
    assert res.json()["is_active"] is False


@pytest.mark.asyncio
async def test_get_nonexistent_member(auth_client):
    res = await auth_client.get("/api/members/999")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_members_require_auth(client):
    res = await client.get("/api/members")
    assert res.status_code in (401, 403)
