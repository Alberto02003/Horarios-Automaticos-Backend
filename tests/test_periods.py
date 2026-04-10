"""Tests for schedule periods and assignments."""

import pytest


@pytest.mark.asyncio
async def test_create_period(auth_client):
    res = await auth_client.post("/api/schedule-periods", json={
        "name": "Abr 2026", "year": 2026, "month": 4, "start_date": "2026-04-01", "end_date": "2026-04-30"
    })
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "draft"
    assert data["name"] == "Abr 2026"


@pytest.mark.asyncio
async def test_activate_period(auth_client):
    create = await auth_client.post("/api/schedule-periods", json={
        "name": "Test", "year": 2026, "month": 5, "start_date": "2026-05-01", "end_date": "2026-05-31"
    })
    pid = create.json()["id"]
    res = await auth_client.patch(f"/api/schedule-periods/{pid}/activate")
    assert res.status_code == 200
    assert res.json()["status"] == "active"


@pytest.mark.asyncio
async def test_cannot_activate_duplicate_month(auth_client):
    # Create and activate first
    p1 = await auth_client.post("/api/schedule-periods", json={"name": "A", "year": 2026, "month": 6, "start_date": "2026-06-01", "end_date": "2026-06-30"})
    await auth_client.patch(f"/api/schedule-periods/{p1.json()['id']}/activate")
    # Create second for same month
    p2 = await auth_client.post("/api/schedule-periods", json={"name": "B", "year": 2026, "month": 6, "start_date": "2026-06-01", "end_date": "2026-06-30"})
    # Try to activate — should fail
    res = await auth_client.patch(f"/api/schedule-periods/{p2.json()['id']}/activate")
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_delete_period(auth_client):
    create = await auth_client.post("/api/schedule-periods", json={
        "name": "Del", "year": 2026, "month": 7, "start_date": "2026-07-01", "end_date": "2026-07-31"
    })
    pid = create.json()["id"]
    res = await auth_client.delete(f"/api/schedule-periods/{pid}")
    assert res.status_code == 204


@pytest.mark.asyncio
async def test_create_assignment(auth_client):
    # Create period + shift type + member
    period = await auth_client.post("/api/schedule-periods", json={"name": "T", "year": 2026, "month": 8, "start_date": "2026-08-01", "end_date": "2026-08-31"})
    shift = await auth_client.post("/api/shift-types", json={"code": "M", "name": "M", "category": "work", "color": "#000"})
    member = await auth_client.post("/api/members", json={"full_name": "X", "role_name": "R", "weekly_hour_limit": 40, "color_tag": "#F00"})

    res = await auth_client.post(f"/api/schedule-periods/{period.json()['id']}/assignments", json={
        "member_id": member.json()["id"], "date": "2026-08-10", "shift_type_id": shift.json()["id"]
    })
    assert res.status_code == 201
    assert res.json()["assignment_source"] == "manual"


@pytest.mark.asyncio
async def test_list_assignments(auth_client):
    period = await auth_client.post("/api/schedule-periods", json={"name": "T", "year": 2026, "month": 9, "start_date": "2026-09-01", "end_date": "2026-09-30"})
    pid = period.json()["id"]
    res = await auth_client.get(f"/api/schedule-periods/{pid}/assignments")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


@pytest.mark.asyncio
async def test_validate_empty_period(auth_client):
    period = await auth_client.post("/api/schedule-periods", json={"name": "V", "year": 2026, "month": 10, "start_date": "2026-10-01", "end_date": "2026-10-31"})
    res = await auth_client.get(f"/api/schedule-periods/{period.json()['id']}/validate")
    assert res.status_code == 200
    assert res.json()["warnings"] == []
