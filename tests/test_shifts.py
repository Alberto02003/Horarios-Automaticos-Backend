"""Tests for shift types CRUD endpoints."""

import pytest


@pytest.mark.asyncio
async def test_create_shift_type(auth_client):
    res = await auth_client.post("/api/shift-types", json={
        "code": "M", "name": "Manana", "category": "work",
        "default_start_time": "07:00", "default_end_time": "15:00", "color": "#3B82F6"
    })
    assert res.status_code == 201
    data = res.json()
    assert data["code"] == "M"
    assert data["default_start_time"] == "07:00"


@pytest.mark.asyncio
async def test_list_shift_types(auth_client):
    await auth_client.post("/api/shift-types", json={"code": "M", "name": "Manana", "category": "work", "color": "#3B82F6"})
    await auth_client.post("/api/shift-types", json={"code": "T", "name": "Tarde", "category": "work", "color": "#F59E0B"})
    res = await auth_client.get("/api/shift-types")
    assert res.status_code == 200
    assert len(res.json()) == 2


@pytest.mark.asyncio
async def test_update_shift_type(auth_client):
    create = await auth_client.post("/api/shift-types", json={"code": "X", "name": "Old", "category": "work", "color": "#000000"})
    sid = create.json()["id"]
    res = await auth_client.put(f"/api/shift-types/{sid}", json={"name": "Updated"})
    assert res.status_code == 200
    assert res.json()["name"] == "Updated"


@pytest.mark.asyncio
async def test_delete_shift_type(auth_client):
    create = await auth_client.post("/api/shift-types", json={"code": "D", "name": "Del", "category": "special", "color": "#999999"})
    sid = create.json()["id"]
    res = await auth_client.delete(f"/api/shift-types/{sid}")
    assert res.status_code == 200
    assert res.json()["is_active"] is False


@pytest.mark.asyncio
async def test_invalid_category(auth_client):
    res = await auth_client.post("/api/shift-types", json={"code": "X", "name": "X", "category": "invalid", "color": "#000"})
    assert res.status_code == 422
