"""CompanySearchService のユニットテスト（RED フェーズ）.

Repository / NL Agent をモックし、ビジネスルールを検証する。
- 自然言語クエリ → LLM Agent で条件抽出 → フィルタ適用
- 解釈失敗（ValueError）は 422 NL_PARSE_FAILED
- LLM 呼び出し失敗（その他例外）は 503 LLM_CALL_FAILED
- 完全一致（company_name / securities_code）は LLM を呼ばない
"""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.api.v1.schemas.company_search import SearchConditionSchema
from app.services.company_search_service import CompanySearchService


class MockNLSearchAgent:
    """テスト用の自然言語検索 Agent."""

    def __call__(self, query: str) -> SearchConditionSchema:
        if "含み益500" in query and "小売" in query:
            return SearchConditionSchema(unrealized_gain_min=500.0, industry="小売")
        elif "PBR" in query:
            return SearchConditionSchema(pbr_max=1.0)
        else:
            raise ValueError("解釈失敗")


def _make_service(agent=None, rows=None, total=0) -> CompanySearchService:
    service = CompanySearchService(
        session=MagicMock(), nl_agent=agent or MockNLSearchAgent()
    )
    service.repo = MagicMock()
    service.repo.find_current_run_id = AsyncMock(return_value=uuid.uuid4())
    service.repo.search_with_filters = AsyncMock(return_value=(rows or [], total))
    return service


# ---------------------------------------------------------------------------
# 自然言語検索: 正常系
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_nl_search_extracts_unrealized_gain_and_industry():
    service = _make_service()
    result = await service.search(q="含み益500億以上の小売業")

    assert result.extracted_filters is not None
    assert result.extracted_filters.unrealized_gain_min == 500.0
    assert result.extracted_filters.industry == "小売"
    assert result.search_summary  # 要約が生成される
    # repo に抽出条件が渡される
    service.repo.search_with_filters.assert_awaited_once()
    _, kwargs = service.repo.search_with_filters.call_args
    conditions = kwargs["conditions"]
    assert conditions.unrealized_gain_min == 500.0
    assert conditions.industry == "小売"


@pytest.mark.asyncio
async def test_nl_search_extracts_pbr():
    service = _make_service()
    result = await service.search(q="PBR1倍割れの企業")
    assert result.extracted_filters.pbr_max == 1.0


# ---------------------------------------------------------------------------
# 自然言語検索: 異常系
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_nl_search_parse_failure_returns_422():
    service = _make_service()
    with pytest.raises(HTTPException) as exc:
        await service.search(q="解釈不能な意味のないクエリ")
    assert exc.value.status_code == 422
    assert exc.value.detail["code"] == "NL_PARSE_FAILED"


@pytest.mark.asyncio
async def test_nl_search_empty_extraction_returns_422():
    """条件が1つも抽出できなかった場合も 422 NL_PARSE_FAILED."""

    class EmptyAgent:
        def __call__(self, query: str) -> SearchConditionSchema:
            return SearchConditionSchema()

    service = _make_service(agent=EmptyAgent())
    with pytest.raises(HTTPException) as exc:
        await service.search(q="何か")
    assert exc.value.status_code == 422
    assert exc.value.detail["code"] == "NL_PARSE_FAILED"


@pytest.mark.asyncio
async def test_nl_search_llm_call_failure_returns_503():
    class FailingAgent:
        def __call__(self, query: str) -> SearchConditionSchema:
            raise RuntimeError("connection error")

    service = _make_service(agent=FailingAgent())
    with pytest.raises(HTTPException) as exc:
        await service.search(q="含み益500億以上の小売業")
    assert exc.value.status_code == 503
    assert exc.value.detail["code"] == "LLM_CALL_FAILED"


@pytest.mark.asyncio
async def test_query_too_long_returns_422():
    service = _make_service()
    with pytest.raises(HTTPException) as exc:
        await service.search(q="あ" * 201)
    assert exc.value.status_code == 422
    assert exc.value.detail["code"] == "QUERY_TOO_LONG"


# ---------------------------------------------------------------------------
# 完全一致検索: LLM を呼ばない
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_exact_match_by_securities_code_skips_llm():
    agent = MagicMock(side_effect=AssertionError("LLM should not be called"))
    service = _make_service(agent=agent)
    result = await service.search(securities_code="1234")
    assert result.search_summary is None
    assert result.extracted_filters is None
    _, kwargs = service.repo.search_with_filters.call_args
    assert kwargs["conditions"].securities_code == "1234"


@pytest.mark.asyncio
async def test_exact_match_by_company_name_skips_llm():
    agent = MagicMock(side_effect=AssertionError("LLM should not be called"))
    service = _make_service(agent=agent)
    await service.search(company_name="テスト不動産")
    _, kwargs = service.repo.search_with_filters.call_args
    assert kwargs["conditions"].company_name == "テスト不動産"


# ---------------------------------------------------------------------------
# スクリーニング未実行: 空レスポンス
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_no_current_run_returns_empty():
    service = _make_service()
    service.repo.find_current_run_id = AsyncMock(return_value=None)
    result = await service.search(securities_code="1234")
    assert result.total == 0
    assert result.items == []
