"""効果検証ダッシュボード・KPI API の統合テスト.

対象エンドポイント:
- GET  /api/v1/kpi/effectiveness
- POST /api/v1/kpi/work-logs
- GET  /api/v1/kpi/work-logs
"""

import uuid
from datetime import date

import pytest
from sqlalchemy import delete

from app.core.database import AsyncSessionLocal
from app.models.kpi import KpiSnapshot, WorkLog


@pytest.fixture
async def clean_work_logs():
    """各テスト前後で work_logs をクリーンにする."""
    async with AsyncSessionLocal() as session:
        await session.execute(delete(WorkLog))
        await session.commit()
    yield
    async with AsyncSessionLocal() as session:
        await session.execute(delete(WorkLog))
        await session.commit()


@pytest.fixture
async def seeded_snapshot():
    """KPI スナップショットを 1 件投入する."""
    snap = KpiSnapshot(
        id=uuid.uuid4(),
        period_from=date(2025, 6, 1),
        period_to=date(2025, 6, 30),
        universe_coverage=100.0,
        traceability_rate=80.0,
        avg_structure_score=55.5,
        reproducibility_score=55.5,
        total_workload_min=1200,
        workload_reduction_rate=96.0,
    )
    async with AsyncSessionLocal() as session:
        session.add(snap)
        await session.commit()
    yield snap
    async with AsyncSessionLocal() as session:
        await session.execute(delete(KpiSnapshot).where(KpiSnapshot.id == snap.id))
        await session.commit()


# ---------------------------------------------------------------------------
# GET /api/v1/kpi/effectiveness
# ---------------------------------------------------------------------------


class TestGetEffectiveness:
    async def test_returns_200_with_latest(self, client, auth_cookies, seeded_snapshot):
        resp = await client.get("/api/v1/kpi/effectiveness", cookies=auth_cookies)
        assert resp.status_code == 200
        data = resp.json()
        assert "snapshots" in data
        assert "latest" in data
        assert data["latest"] is not None
        assert "universe_coverage" in data["latest"]
        assert "traceability_rate" in data["latest"]
        assert "avg_structure_score" in data["latest"]
        assert "reproducibility_score" in data["latest"]
        assert "workload_reduction_rate" in data["latest"]

    async def test_period_filter(self, client, auth_cookies, seeded_snapshot):
        resp = await client.get(
            "/api/v1/kpi/effectiveness",
            params={"period_from": "2025-06-01", "period_to": "2025-06-30"},
            cookies=auth_cookies,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["snapshots"]) >= 1

    async def test_period_filter_excludes_out_of_range(
        self, client, auth_cookies, seeded_snapshot
    ):
        resp = await client.get(
            "/api/v1/kpi/effectiveness",
            params={"period_from": "2025-01-01", "period_to": "2025-01-31"},
            cookies=auth_cookies,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["snapshots"] == []

    async def test_unauthorized_returns_401(self, client):
        resp = await client.get("/api/v1/kpi/effectiveness")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# POST /api/v1/kpi/work-logs
# ---------------------------------------------------------------------------


class TestCreateWorkLog:
    async def test_create_returns_201(self, client, auth_cookies, clean_work_logs):
        payload = {
            "task_type": "primary_screening",
            "duration_min": 90,
            "logged_on": "2025-06-26",
        }
        resp = await client.post(
            "/api/v1/kpi/work-logs", json=payload, cookies=auth_cookies
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["task_type"] == "primary_screening"
        assert data["duration_min"] == 90
        assert data["logged_on"] == "2025-06-26"
        assert "id" in data
        assert "user_id" in data

    async def test_create_invalid_task_type_returns_422(
        self, client, auth_cookies, clean_work_logs
    ):
        payload = {
            "task_type": "invalid_type",
            "duration_min": 90,
            "logged_on": "2025-06-26",
        }
        resp = await client.post(
            "/api/v1/kpi/work-logs", json=payload, cookies=auth_cookies
        )
        assert resp.status_code == 422

    async def test_create_non_positive_duration_returns_422(
        self, client, auth_cookies, clean_work_logs
    ):
        payload = {
            "task_type": "report",
            "duration_min": 0,
            "logged_on": "2025-06-26",
        }
        resp = await client.post(
            "/api/v1/kpi/work-logs", json=payload, cookies=auth_cookies
        )
        assert resp.status_code == 422

    async def test_create_unauthorized_returns_401(self, client):
        payload = {
            "task_type": "report",
            "duration_min": 30,
            "logged_on": "2025-06-26",
        }
        resp = await client.post("/api/v1/kpi/work-logs", json=payload)
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/v1/kpi/work-logs
# ---------------------------------------------------------------------------


class TestListWorkLogs:
    async def test_list_returns_items_and_total(
        self, client, auth_cookies, clean_work_logs
    ):
        for minutes in (60, 30):
            await client.post(
                "/api/v1/kpi/work-logs",
                json={
                    "task_type": "deep_dive",
                    "duration_min": minutes,
                    "logged_on": "2025-06-26",
                },
                cookies=auth_cookies,
            )
        resp = await client.get("/api/v1/kpi/work-logs", cookies=auth_cookies)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_min"] == 90
        assert len(data["items"]) == 2

    async def test_list_range_filter(self, client, auth_cookies, clean_work_logs):
        await client.post(
            "/api/v1/kpi/work-logs",
            json={
                "task_type": "other",
                "duration_min": 45,
                "logged_on": "2025-05-01",
            },
            cookies=auth_cookies,
        )
        await client.post(
            "/api/v1/kpi/work-logs",
            json={
                "task_type": "other",
                "duration_min": 15,
                "logged_on": "2025-06-26",
            },
            cookies=auth_cookies,
        )
        resp = await client.get(
            "/api/v1/kpi/work-logs",
            params={"from": "2025-06-01", "to": "2025-06-30"},
            cookies=auth_cookies,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_min"] == 15
        assert len(data["items"]) == 1

    async def test_list_unauthorized_returns_401(self, client):
        resp = await client.get("/api/v1/kpi/work-logs")
        assert resp.status_code == 401
