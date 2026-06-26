"""直近イベント API の統合テスト.

対象エンドポイント:
- GET /api/v1/events/recent
"""

import uuid
from datetime import date, datetime, timedelta

import pytest
from sqlalchemy import delete

from app.core.database import AsyncSessionLocal
from app.models.company import Company, Event


@pytest.fixture
async def seeded_events():
    """企業 1 件と、直近・古いイベントを投入する."""
    company = Company(
        id=uuid.uuid4(),
        securities_code="T9999",
        name="テスト直近イベント株式会社",
        industry="不動産",
        market_cap=1000.0,
        is_universe=True,
    )
    recent_event = Event(
        id=uuid.uuid4(),
        company_id=company.id,
        document_id=None,
        event_type="new_disclosure",
        occurred_at=date.today() - timedelta(days=1),
        created_at=datetime.now(),
    )
    old_event = Event(
        id=uuid.uuid4(),
        company_id=company.id,
        document_id=None,
        event_type="large_shareholding",
        occurred_at=date.today() - timedelta(days=30),
        created_at=datetime.now(),
    )
    async with AsyncSessionLocal() as session:
        session.add(company)
        session.add(recent_event)
        session.add(old_event)
        await session.commit()
    yield {
        "company_id": company.id,
        "recent_event_id": recent_event.id,
        "old_event_id": old_event.id,
    }
    async with AsyncSessionLocal() as session:
        await session.execute(delete(Event).where(Event.company_id == company.id))
        await session.execute(delete(Company).where(Company.id == company.id))
        await session.commit()


class TestGetRecentEvents:
    async def test_returns_200_and_recent_events(
        self, client, auth_cookies, seeded_events
    ):
        resp = await client.get("/api/v1/events/recent", cookies=auth_cookies)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        codes = {item["securities_code"] for item in data}
        assert "T9999" in codes
        item = next(i for i in data if i["securities_code"] == "T9999")
        assert item["event_type"] == "new_disclosure"
        assert item["company_name"] == "テスト直近イベント株式会社"
        assert "occurred_at" in item
        assert "event_score" in item

    async def test_excludes_events_older_than_7_days(
        self, client, auth_cookies, seeded_events
    ):
        resp = await client.get("/api/v1/events/recent", cookies=auth_cookies)
        assert resp.status_code == 200
        data = resp.json()
        # 30 日前の large_shareholding は対象外
        types = {i["event_type"] for i in data if i["securities_code"] == "T9999"}
        assert "large_shareholding" not in types

    async def test_unauthorized_returns_401(self, client):
        resp = await client.get("/api/v1/events/recent")
        assert resp.status_code == 401
