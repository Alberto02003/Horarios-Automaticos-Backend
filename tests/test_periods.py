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
async def test_cannot_create_duplicate_active_month(auth_client):
    # Create and activate first
    p1 = await auth_client.post("/api/schedule-periods", json={"name": "A", "year": 2026, "month": 6, "start_date": "2026-06-01", "end_date": "2026-06-30"})
    await auth_client.patch(f"/api/schedule-periods/{p1.json()['id']}/activate")
    # Try to create second for same month — should fail
    p2 = await auth_client.post("/api/schedule-periods", json={"name": "B", "year": 2026, "month": 6, "start_date": "2026-06-01", "end_date": "2026-06-30"})
    assert p2.status_code == 400


@pytest.mark.asyncio
async def test_delete_period(auth_client):
    create = await auth_client.post("/api/schedule-periods", json={
        "name": "Del", "year": 2026, "month": 7, "start_date": "2026-07-01", "end_date": "2026-07-31"
    })
    pid = create.json()["id"]
    res = await auth_client.delete(f"/api/schedule-periods/{pid}")
    assert res.status_code == 200
    assert res.json()["is_active"] is False


@pytest.mark.asyncio
async def test_create_assignment(auth_client):
    # Create period + shift type + member
    period = await auth_client.post("/api/schedule-periods", json={"name": "T", "year": 2026, "month": 8, "start_date": "2026-08-01", "end_date": "2026-08-31"})
    shift = await auth_client.post("/api/shift-types", json={"code": "M", "name": "Manana", "category": "work", "color": "#3B82F6"})
    member = await auth_client.post("/api/members", json={"full_name": "Worker", "role_name": "Role", "weekly_hour_limit": 40, "color_tag": "#F472B6"})

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
async def test_bulk_update_assignments(auth_client):
    period = await auth_client.post("/api/schedule-periods", json={"name": "BU", "year": 2027, "month": 1, "start_date": "2027-01-01", "end_date": "2027-01-31"})
    pid = period.json()["id"]
    shift1 = await auth_client.post("/api/shift-types", json={"code": "BM", "name": "BulkM", "category": "work", "color": "#3B82F6"})
    shift2 = await auth_client.post("/api/shift-types", json={"code": "BT", "name": "BulkT", "category": "work", "color": "#F59E0B"})
    member = await auth_client.post("/api/members", json={"full_name": "Bulk Worker", "role_name": "R", "weekly_hour_limit": 40, "color_tag": "#F472B6"})
    mid = member.json()["id"]
    sid1 = shift1.json()["id"]
    sid2 = shift2.json()["id"]

    a1 = await auth_client.post(f"/api/schedule-periods/{pid}/assignments", json={"member_id": mid, "date": "2027-01-05", "shift_type_id": sid1})
    a2 = await auth_client.post(f"/api/schedule-periods/{pid}/assignments", json={"member_id": mid, "date": "2027-01-06", "shift_type_id": sid1})
    ids = [a1.json()["id"], a2.json()["id"]]

    res = await auth_client.put(f"/api/schedule-periods/{pid}/assignments/bulk", json={"ids": ids, "shift_type_id": sid2})
    assert res.status_code == 200
    assert all(a["shift_type_id"] == sid2 for a in res.json())


@pytest.mark.asyncio
async def test_bulk_delete_assignments(auth_client):
    period = await auth_client.post("/api/schedule-periods", json={"name": "BD", "year": 2027, "month": 2, "start_date": "2027-02-01", "end_date": "2027-02-28"})
    pid = period.json()["id"]
    shift = await auth_client.post("/api/shift-types", json={"code": "BD", "name": "BDel", "category": "work", "color": "#3B82F6"})
    member = await auth_client.post("/api/members", json={"full_name": "Del Worker", "role_name": "R", "weekly_hour_limit": 40, "color_tag": "#F472B6"})
    mid = member.json()["id"]
    sid = shift.json()["id"]

    a1 = await auth_client.post(f"/api/schedule-periods/{pid}/assignments", json={"member_id": mid, "date": "2027-02-10", "shift_type_id": sid})
    a2 = await auth_client.post(f"/api/schedule-periods/{pid}/assignments", json={"member_id": mid, "date": "2027-02-11", "shift_type_id": sid})

    res = await auth_client.request("DELETE", f"/api/schedule-periods/{pid}/assignments/bulk", json={"ids": [a1.json()["id"], a2.json()["id"]]})
    assert res.status_code == 200
    assert res.json()["deleted"] == 2

    remaining = await auth_client.get(f"/api/schedule-periods/{pid}/assignments")
    assert len(remaining.json()) == 0


@pytest.mark.asyncio
async def test_bulk_delete_skips_locked(auth_client):
    period = await auth_client.post("/api/schedule-periods", json={"name": "BL", "year": 2027, "month": 3, "start_date": "2027-03-01", "end_date": "2027-03-31"})
    pid = period.json()["id"]
    shift = await auth_client.post("/api/shift-types", json={"code": "BL", "name": "BLock", "category": "work", "color": "#3B82F6"})
    member = await auth_client.post("/api/members", json={"full_name": "Lock Worker", "role_name": "R", "weekly_hour_limit": 40, "color_tag": "#F472B6"})
    mid = member.json()["id"]
    sid = shift.json()["id"]

    a1 = await auth_client.post(f"/api/schedule-periods/{pid}/assignments", json={"member_id": mid, "date": "2027-03-10", "shift_type_id": sid})
    aid = a1.json()["id"]
    # Lock it
    await auth_client.put(f"/api/schedule-periods/{pid}/assignments/{aid}", json={"is_locked": True})

    res = await auth_client.request("DELETE", f"/api/schedule-periods/{pid}/assignments/bulk", json={"ids": [aid]})
    assert res.status_code == 200
    assert res.json()["deleted"] == 0


@pytest.mark.asyncio
async def test_validate_empty_period(auth_client):
    period = await auth_client.post("/api/schedule-periods", json={"name": "V", "year": 2026, "month": 10, "start_date": "2026-10-01", "end_date": "2026-10-31"})
    res = await auth_client.get(f"/api/schedule-periods/{period.json()['id']}/validate")
    assert res.status_code == 200
    assert res.json()["warnings"] == []
