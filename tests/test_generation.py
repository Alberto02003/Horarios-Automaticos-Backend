"""Tests for schedule generation and preferences."""

import pytest


@pytest.mark.asyncio
async def test_get_global_preferences(auth_client):
    res = await auth_client.get("/api/preferences")
    assert res.status_code == 200
    data = res.json()
    assert "general_weekly_hour_limit" in data
    assert "preferences_jsonb" in data


@pytest.mark.asyncio
async def test_update_preferences(auth_client):
    res = await auth_client.put("/api/preferences", json={
        "general_weekly_hour_limit": 35,
        "preferences_jsonb": {"min_rest_hours": 10, "max_consecutive_days": 5, "allow_weekend_work": False}
    })
    assert res.status_code == 200
    assert res.json()["general_weekly_hour_limit"] == 35.0


@pytest.mark.asyncio
async def test_generate_balanced(auth_client):
    # Setup: period + member + shift type
    period = await auth_client.post("/api/schedule-periods", json={"name": "Gen", "year": 2026, "month": 11, "start_date": "2026-11-01", "end_date": "2026-11-30"})
    await auth_client.post("/api/members", json={"full_name": "Worker", "role_name": "Role", "weekly_hour_limit": 40, "color_tag": "#F472B6"})
    await auth_client.post("/api/shift-types", json={"code": "M", "name": "Manana", "category": "work", "default_start_time": "07:00", "default_end_time": "15:00", "color": "#3B82F6"})
    await auth_client.post("/api/shift-types", json={"code": "D", "name": "Descanso", "category": "special", "color": "#10B981", "counts_as_work_time": False})

    res = await auth_client.post(f"/api/schedule-periods/{period.json()['id']}/generate", json={
        "strategy": "balanced", "fill_unassigned_only": True
    })
    assert res.status_code == 200
    data = res.json()
    assert data["strategy"] == "balanced"
    assert data["created_count"] > 0


@pytest.mark.asyncio
async def test_generate_invalid_strategy(auth_client):
    period = await auth_client.post("/api/schedule-periods", json={"name": "Bad", "year": 2026, "month": 12, "start_date": "2026-12-01", "end_date": "2026-12-31"})
    res = await auth_client.post(f"/api/schedule-periods/{period.json()['id']}/generate", json={
        "strategy": "nonexistent"
    })
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_cannot_generate_active_period(auth_client):
    period = await auth_client.post("/api/schedule-periods", json={"name": "Act", "year": 2027, "month": 1, "start_date": "2027-01-01", "end_date": "2027-01-31"})
    pid = period.json()["id"]
    await auth_client.patch(f"/api/schedule-periods/{pid}/activate")
    res = await auth_client.post(f"/api/schedule-periods/{pid}/generate", json={"strategy": "balanced"})
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_generation_runs_history(auth_client):
    period = await auth_client.post("/api/schedule-periods", json={"name": "Hist", "year": 2027, "month": 2, "start_date": "2027-02-01", "end_date": "2027-02-28"})
    pid = period.json()["id"]
    res = await auth_client.get(f"/api/schedule-periods/{pid}/generation-runs")
    assert res.status_code == 200
    assert isinstance(res.json(), list)
