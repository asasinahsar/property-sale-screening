"""企業詳細・根拠レポート API の統合テスト（RED フェーズ）.

実 DB（シードデータ）に接続し、HTTP リクエスト/レスポンスを検証する。
対象エンドポイント:
- GET  /api/v1/companies/{id}
- POST /api/v1/companies/{id}/report
- GET  /api/v1/files/{id}
"""

import uuid
from datetime import datetime

import pytest
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.company import Company


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
async def generated_file_id(analyst_user):
    """テスト用の GeneratedFile を作成して ID を返す."""
    from app.models.longlist import GeneratedFile

    async with AsyncSessionLocal() as session:
        gen_file = GeneratedFile(
            id=uuid.uuid4(),
            created_by=analyst_user.id,
            company_id=None,
            file_kind="report",
            format="pdf",
            s3_key="reports/test.pdf",
            created_at=datetime(2025, 6, 25, 12, 0, 0),
        )
        session.add(gen_file)
        await session.commit()
        await session.refresh(gen_file)
        return gen_file.id


# ---------------------------------------------------------------------------
# GET /api/v1/companies/{id}
# ---------------------------------------------------------------------------


class TestGetCompanyDetail:
    """企業詳細取得エンドポイントのテスト."""

    async def test_get_company_detail_returns_200(
        self, client, auth_cookies, seeded_company_id
    ):
        """有効な company_id で 200 が返ること."""
        resp = await client.get(
            f"/api/v1/companies/{seeded_company_id}", cookies=auth_cookies
        )
        assert resp.status_code == 200

    async def test_get_company_detail_response_structure(
        self, client, auth_cookies, seeded_company_id
    ):
        """レスポンスに必須フィールドが含まれること."""
        resp = await client.get(
            f"/api/v1/companies/{seeded_company_id}", cookies=auth_cookies
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "company_id" in data
        assert "name" in data
        assert "industry" in data
        assert "scoring" in data
        assert "financial" in data
        assert "signals_support" in data
        assert "signals_counter" in data
        assert isinstance(data["signals_support"], list)
        assert isinstance(data["signals_counter"], list)

    async def test_get_company_detail_not_found_returns_404(self, client, auth_cookies):
        """存在しない UUID で 404 が返ること."""
        random_id = uuid.uuid4()
        resp = await client.get(f"/api/v1/companies/{random_id}", cookies=auth_cookies)
        assert resp.status_code == 404

    async def test_get_company_detail_unauthorized_returns_401(
        self, client, seeded_company_id
    ):
        """トークンなしで 401 が返ること."""
        resp = await client.get(f"/api/v1/companies/{seeded_company_id}")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# POST /api/v1/companies/{id}/report
# ---------------------------------------------------------------------------


class TestPostReport:
    """根拠レポート生成エンドポイントのテスト."""

    async def test_post_report_returns_202(
        self, client, auth_cookies, seeded_company_id
    ):
        """有効な company_id + format=pdf で 202 + file_id が返ること."""
        resp = await client.post(
            f"/api/v1/companies/{seeded_company_id}/report",
            json={"format": "pdf"},
            cookies=auth_cookies,
        )
        assert resp.status_code == 202
        data = resp.json()
        assert "file_id" in data
        assert data["status"] == "pending"

    async def test_post_report_not_found_returns_404(self, client, auth_cookies):
        """存在しない company_id で 404 が返ること."""
        random_id = uuid.uuid4()
        resp = await client.post(
            f"/api/v1/companies/{random_id}/report",
            json={"format": "pdf"},
            cookies=auth_cookies,
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/v1/files/{id}
# ---------------------------------------------------------------------------


class TestGetFileStatus:
    """ファイル生成ステータス取得エンドポイントのテスト."""

    async def test_get_file_status_returns_200(
        self, client, auth_cookies, generated_file_id
    ):
        """有効な file_id で 200 + status が返ること."""
        resp = await client.get(
            f"/api/v1/files/{generated_file_id}", cookies=auth_cookies
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "file_id" in data

    async def test_get_file_status_not_found_returns_404(self, client, auth_cookies):
        """存在しない file_id で 404 が返ること."""
        random_id = uuid.uuid4()
        resp = await client.get(f"/api/v1/files/{random_id}", cookies=auth_cookies)
        assert resp.status_code == 404
