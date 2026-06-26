"""CompanySearchService - 企業検索（完全一致＋自然言語）のビジネスロジック.

自然言語クエリの場合は LLM Agent で検索条件を抽出し、収集済みデータに適用する。
LLM 呼び出しはこのサービス層に閉じ込める。
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.company_search import (
    CompanySearchResponse,
    SearchConditionSchema,
)
from app.api.v1.schemas.scoring import (
    CompanyRankingItemSchema,
    ConfidenceLevelEnum,
)
from app.repositories.company_repository import CompanyRepository

MAX_QUERY_LENGTH = 200


def _http_error(status_code: int, code: str, message: str):
    from fastapi import HTTPException

    return HTTPException(
        status_code=status_code, detail={"code": code, "message": message}
    )


class CompanySearchService:
    """企業検索サービス."""

    def __init__(self, session: AsyncSession, nl_agent) -> None:
        self.session = session
        self.nl_agent = nl_agent
        self.repo = CompanyRepository(session)

    async def search(
        self,
        *,
        q: str | None = None,
        company_name: str | None = None,
        securities_code: str | None = None,
        industry: str | None = None,
        sort_by: str = "total_score",
        page: int = 1,
        page_size: int = 20,
    ) -> CompanySearchResponse:
        """企業を検索する。

        - q（自然言語）が指定された場合: LLM Agent で条件抽出 → フィルタ適用
        - company_name / securities_code: 完全一致
        """
        search_summary: str | None = None
        extracted_filters: SearchConditionSchema | None = None

        if q is not None and q.strip() != "":
            if len(q) > MAX_QUERY_LENGTH:
                raise _http_error(
                    422,
                    "QUERY_TOO_LONG",
                    f"検索クエリは{MAX_QUERY_LENGTH}字以内で入力してください",
                )
            extracted_filters = self._extract_filters(q)
            search_summary = self._build_summary(extracted_filters)
            conditions = extracted_filters.model_copy()
        else:
            conditions = SearchConditionSchema()

        # 明示指定された完全一致条件をマージ（優先）
        if company_name is not None:
            conditions.company_name = company_name
        if securities_code is not None:
            conditions.securities_code = securities_code
        if industry is not None:
            conditions.industry = industry

        # 現在の有効なスクリーニング run を取得
        run_id = await self.repo.find_current_run_id()
        if run_id is None:
            return CompanySearchResponse(
                items=[],
                total=0,
                page=page,
                page_size=page_size,
                search_summary=search_summary,
                extracted_filters=extracted_filters,
            )

        rows, total = await self.repo.search_with_filters(
            run_id,
            conditions=conditions,
            sort_by=sort_by,
            page=page,
            page_size=page_size,
        )

        items = [self._row_to_item(row) for row in rows]
        return CompanySearchResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            search_summary=search_summary,
            extracted_filters=extracted_filters,
        )

    # ------------------------------------------------------------------
    # ヘルパー
    # ------------------------------------------------------------------

    def _extract_filters(self, q: str) -> SearchConditionSchema:
        """LLM Agent で条件を抽出する。失敗時は適切な HTTPException を送出."""
        try:
            conditions = self.nl_agent(q)
        except ValueError as e:
            raise _http_error(422, "NL_PARSE_FAILED", "条件の解釈に失敗しました") from e
        except Exception as e:  # noqa: BLE001 - LLM 呼び出し失敗を 503 に変換
            raise _http_error(
                503, "LLM_CALL_FAILED", f"LLM 呼び出しに失敗しました: {e}"
            ) from e

        if conditions.is_empty():
            raise _http_error(422, "NL_PARSE_FAILED", "条件の解釈に失敗しました")
        return conditions

    @staticmethod
    def _build_summary(conditions: SearchConditionSchema) -> str:
        """抽出条件から人間可読な要約文を生成する."""
        parts: list[str] = []
        if conditions.industry:
            parts.append(f"業種=「{conditions.industry}」")
        if conditions.region:
            parts.append(f"地域=「{conditions.region}」")
        if conditions.unrealized_gain_min is not None:
            parts.append(f"含み益{conditions.unrealized_gain_min:g}億円以上")
        if conditions.unrealized_gain_max is not None:
            parts.append(f"含み益{conditions.unrealized_gain_max:g}億円以下")
        if conditions.pbr_max is not None:
            parts.append(f"PBR{conditions.pbr_max:g}倍以下")
        if conditions.pbr_min is not None:
            parts.append(f"PBR{conditions.pbr_min:g}倍以上")
        if conditions.structure_score_min is not None:
            parts.append(f"構造スコア{conditions.structure_score_min:g}以上")
        if conditions.company_name:
            parts.append(f"企業名「{conditions.company_name}」")
        if conditions.securities_code:
            parts.append(f"証券コード「{conditions.securities_code}」")

        if not parts:
            return "条件を抽出できませんでした"
        return "、".join(parts) + " で絞り込みました"

    @staticmethod
    def _row_to_item(row: dict) -> CompanyRankingItemSchema:
        return CompanyRankingItemSchema(
            company_id=row["company_id"],
            securities_code=row["securities_code"],
            name=row["name"],
            industry=row["industry"],
            market_cap=float(row["market_cap"])
            if row.get("market_cap") is not None
            else None,
            total_score=float(row["total_score"]),
            structure_score=float(row["structure_score"]),
            event_score=float(row["event_score"]),
            event_boost=float(row["event_boost"])
            if row.get("event_boost") is not None
            else None,
            confidence=ConfidenceLevelEnum(row["confidence"]),
            unrealized_gain=float(row["unrealized_gain"])
            if row.get("unrealized_gain") is not None
            else None,
            has_event=bool(row.get("has_event")),
        )
