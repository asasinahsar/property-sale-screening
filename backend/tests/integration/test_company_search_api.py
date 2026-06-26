"""企業検索 API（GET /api/v1/companies?q= / company_name / securities_code）の統合テスト.

実 DB（シードデータ）に接続し、HTTP リクエスト/レスポンスを検証する。
自然言語検索の LLM 呼び出しはモック Agent を dependency_overrides で差し替える。
"""

import pytest
from sqlalchemy import select

from app.api.v1.dependencies.search import get_nl_search_agent
from app.api.v1.schemas.company_search import SearchConditionSchema
from app.core.database import AsyncSessionLocal
from app.main import app
from app.models.company import Company


class MockNLSearchAgent:
    def __call__(self, query: str) -> SearchConditionSchema:
        if "含み益500" in query and "小売" in query:
            return SearchConditionSchema(unrealized_gain_min=500.0, industry="小売")
        elif "PBR" in query:
            return SearchConditionSchema(pbr_max=1.0)
        else:
            raise ValueError("解釈失敗")


@pytest.fixture
def mock_nl_agent():
    app.dependency_overrides[get_nl_search_agent] = lambda: MockNLSearchAgent()
    yield
    app.dependency_overrides.pop(get_nl_search_agent, None)


@pytest.fixture
async def seeded_company():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Company).limit(1))
        company = result.scalars().first()
        if company is None:
            pytest.skip("シード企業データが存在しないためスキップ")
        return company


class TestNaturalLanguageSearch:
    async def test_nl_search_returns_summary_and_filters(
        self, client, auth_cookies, mock_nl_agent
    ):
        resp = await client.get(
            "/api/v1/companies",
            params={"q": "含み益500億以上の小売業"},
            cookies=auth_cookies,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert data["search_summary"]
        assert data["extracted_filters"]["unrealized_gain_min"] == 500.0
        assert data["extracted_filters"]["industry"] == "小売"

    async def test_nl_search_parse_failure_returns_422(
        self, client, auth_cookies, mock_nl_agent
    ):
        resp = await client.get(
            "/api/v1/companies",
            params={"q": "意味のわからないクエリ"},
            cookies=auth_cookies,
        )
        assert resp.status_code == 422
        assert resp.json()["detail"]["code"] == "NL_PARSE_FAILED"

    async def test_nl_search_query_too_long_returns_422(
        self, client, auth_cookies, mock_nl_agent
    ):
        resp = await client.get(
            "/api/v1/companies",
            params={"q": "あ" * 201},
            cookies=auth_cookies,
        )
        assert resp.status_code == 422

    async def test_nl_search_unauthorized_returns_401(self, client, mock_nl_agent):
        resp = await client.get("/api/v1/companies", params={"q": "PBR1倍割れ"})
        assert resp.status_code == 401


class TestExactMatchSearch:
    async def test_exact_match_by_securities_code(
        self, client, auth_cookies, seeded_company
    ):
        resp = await client.get(
            "/api/v1/companies",
            params={"securities_code": seeded_company.securities_code},
            cookies=auth_cookies,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["search_summary"] is None
        codes = {item["securities_code"] for item in data["items"]}
        # スコアリング結果が存在する場合のみ一致企業が返る
        assert codes <= {seeded_company.securities_code}

    async def test_exact_match_by_company_name(
        self, client, auth_cookies, seeded_company
    ):
        resp = await client.get(
            "/api/v1/companies",
            params={"company_name": seeded_company.name},
            cookies=auth_cookies,
        )
        assert resp.status_code == 200
        names = {item["name"] for item in resp.json()["items"]}
        assert names <= {seeded_company.name}


class TestRankingUnaffected:
    """検索パラメータ無しの既存ランキング動作は維持される."""

    async def test_plain_ranking_still_works(self, client, auth_cookies):
        resp = await client.get(
            "/api/v1/companies",
            params={"page": 1, "page_size": 20},
            cookies=auth_cookies,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert data["search_summary"] is None
