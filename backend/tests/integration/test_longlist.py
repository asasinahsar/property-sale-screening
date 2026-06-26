"""ロングリスト管理・承認フロー＆エクスポート API の統合テスト（RED フェーズ）.

実 DB（シードデータ）に接続し、HTTP リクエスト/レスポンスを検証する。
対象エンドポイント:
- GET    /api/v1/longlist
- POST   /api/v1/longlist
- PATCH  /api/v1/longlist/{id}
- POST   /api/v1/longlist/{id}/approval
- DELETE /api/v1/longlist/{id}
- POST   /api/v1/longlist/export
"""

import uuid

import pytest
from sqlalchemy import delete, select

from app.core.database import AsyncSessionLocal
from app.models.company import Company
from app.models.longlist import LonglistItem


@pytest.fixture
async def seeded_company_id():
    """シード済みの企業 ID を1件取得する（存在しなければ skip）."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Company).limit(1))
        company = result.scalars().first()
        if company is None:
            pytest.skip("シード企業データが存在しないためスキップ")
        return company.id


@pytest.fixture
async def clean_longlist():
    """各テスト前後で longlist_items をクリーンにする."""
    async with AsyncSessionLocal() as session:
        await session.execute(delete(LonglistItem))
        await session.commit()
    yield
    async with AsyncSessionLocal() as session:
        await session.execute(delete(LonglistItem))
        await session.commit()


# ---------------------------------------------------------------------------
# GET /api/v1/longlist
# ---------------------------------------------------------------------------


class TestGetLonglist:
    async def test_get_longlist_returns_200(self, client, auth_cookies, clean_longlist):
        resp = await client.get("/api/v1/longlist", cookies=auth_cookies)
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)

    async def test_get_longlist_unauthorized_returns_401(self, client):
        resp = await client.get("/api/v1/longlist")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# POST /api/v1/longlist
# ---------------------------------------------------------------------------


class TestAddLonglist:
    async def test_add_returns_201(
        self, client, auth_cookies, seeded_company_id, clean_longlist
    ):
        resp = await client.post(
            "/api/v1/longlist",
            json={"company_id": str(seeded_company_id)},
            cookies=auth_cookies,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["company_id"] == str(seeded_company_id)
        assert data["status"] == "candidate"

    async def test_add_duplicate_returns_409(
        self, client, auth_cookies, seeded_company_id, clean_longlist
    ):
        await client.post(
            "/api/v1/longlist",
            json={"company_id": str(seeded_company_id)},
            cookies=auth_cookies,
        )
        resp = await client.post(
            "/api/v1/longlist",
            json={"company_id": str(seeded_company_id)},
            cookies=auth_cookies,
        )
        assert resp.status_code == 409


# ---------------------------------------------------------------------------
# PATCH /api/v1/longlist/{id}
# ---------------------------------------------------------------------------


class TestUpdateLonglist:
    async def test_update_memo_returns_200(
        self, client, auth_cookies, seeded_company_id, clean_longlist
    ):
        created = await client.post(
            "/api/v1/longlist",
            json={"company_id": str(seeded_company_id)},
            cookies=auth_cookies,
        )
        item_id = created.json()["id"]
        resp = await client.patch(
            f"/api/v1/longlist/{item_id}",
            json={"reason_memo": "含み益が大きく割安"},
            cookies=auth_cookies,
        )
        assert resp.status_code == 200
        assert resp.json()["reason_memo"] == "含み益が大きく割安"

    async def test_update_not_found_returns_404(self, client, auth_cookies):
        resp = await client.patch(
            f"/api/v1/longlist/{uuid.uuid4()}",
            json={"reason_memo": "x"},
            cookies=auth_cookies,
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/v1/longlist/{id}/approval
# ---------------------------------------------------------------------------


class TestApproval:
    async def test_approve_by_manager_returns_200(
        self, client, auth_cookies, manager_cookies, seeded_company_id, clean_longlist
    ):
        created = await client.post(
            "/api/v1/longlist",
            json={"company_id": str(seeded_company_id)},
            cookies=auth_cookies,
        )
        item_id = created.json()["id"]
        resp = await client.post(
            f"/api/v1/longlist/{item_id}/approval",
            json={"action": "approve"},
            cookies=manager_cookies,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "approved"

    async def test_approve_by_analyst_returns_403(
        self, client, auth_cookies, seeded_company_id, clean_longlist
    ):
        created = await client.post(
            "/api/v1/longlist",
            json={"company_id": str(seeded_company_id)},
            cookies=auth_cookies,
        )
        item_id = created.json()["id"]
        resp = await client.post(
            f"/api/v1/longlist/{item_id}/approval",
            json={"action": "approve"},
            cookies=auth_cookies,
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# DELETE /api/v1/longlist/{id}
# ---------------------------------------------------------------------------


class TestDelete:
    async def test_delete_returns_204(
        self, client, auth_cookies, seeded_company_id, clean_longlist
    ):
        created = await client.post(
            "/api/v1/longlist",
            json={"company_id": str(seeded_company_id)},
            cookies=auth_cookies,
        )
        item_id = created.json()["id"]
        resp = await client.delete(f"/api/v1/longlist/{item_id}", cookies=auth_cookies)
        assert resp.status_code == 204

    async def test_delete_not_found_returns_404(self, client, auth_cookies):
        resp = await client.delete(
            f"/api/v1/longlist/{uuid.uuid4()}", cookies=auth_cookies
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/v1/longlist/export
# ---------------------------------------------------------------------------


class TestExport:
    async def test_export_returns_202(
        self, client, auth_cookies, seeded_company_id, clean_longlist
    ):
        await client.post(
            "/api/v1/longlist",
            json={"company_id": str(seeded_company_id)},
            cookies=auth_cookies,
        )
        resp = await client.post("/api/v1/longlist/export", cookies=auth_cookies)
        assert resp.status_code == 202
        data = resp.json()
        assert "file_id" in data
        assert data["status"] == "pending"

    async def test_export_empty_returns_409(self, client, auth_cookies, clean_longlist):
        resp = await client.post("/api/v1/longlist/export", cookies=auth_cookies)
        assert resp.status_code == 409
