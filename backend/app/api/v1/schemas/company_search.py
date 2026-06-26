"""企業検索（完全一致＋自然言語）関連スキーマ（Pydantic v2 DTO）.

P001 機能6: 企業検索。
- 自然言語クエリ（最大200字）から検索条件を抽出
- 完全一致（企業名 / 証券コード）
"""

from pydantic import BaseModel, ConfigDict, Field

from app.api.v1.schemas.scoring import CompanyRankingItemSchema


class SearchConditionSchema(BaseModel):
    """自然言語クエリから抽出された検索条件（フィルタ）.

    全フィールド optional。未抽出のフィールドは None。
    """

    model_config = ConfigDict(extra="ignore")

    unrealized_gain_min: float | None = Field(
        default=None, description="含み益下限（億円）"
    )
    unrealized_gain_max: float | None = Field(
        default=None, description="含み益上限（億円）"
    )
    region: str | None = Field(default=None, description="地域（例：関西）")
    industry: str | None = Field(default=None, description="業種（例：小売）")
    pbr_max: float | None = Field(default=None, description="PBR 上限（例：1.0）")
    pbr_min: float | None = Field(default=None, description="PBR 下限")
    structure_score_min: float | None = Field(
        default=None, description="構造スコア下限"
    )
    company_name: str | None = Field(default=None, description="企業名（完全一致）")
    securities_code: str | None = Field(
        default=None, description="証券コード（完全一致）"
    )

    def is_empty(self) -> bool:
        """有効な条件が1つも抽出されていない場合 True."""
        return all(value is None for value in self.model_dump().values())


class NLSearchRequestSchema(BaseModel):
    """自然言語検索リクエスト."""

    query: str = Field(..., max_length=200, description="検索クエリ（最大200字）")


class NLSearchResponseSchema(BaseModel):
    """自然言語検索の抽出結果（条件＋要約）."""

    extracted_filters: SearchConditionSchema = Field(
        ..., description="抽出された検索条件"
    )
    summary: str = Field(..., description="抽出結果の説明")
    items_count: int = Field(..., ge=0, description="マッチ企業数")


class CompanySearchResponse(BaseModel):
    """企業検索レスポンス（ランキング一覧 + 自然言語検索の要約付き）.

    完全一致・通常フィルタの場合 search_summary / extracted_filters は None。
    """

    items: list[CompanyRankingItemSchema] = Field(
        default_factory=list, description="一致した企業一覧"
    )
    total: int = Field(..., ge=0, description="総件数")
    page: int = Field(..., ge=1, description="現在ページ番号（1始まり）")
    page_size: int = Field(..., ge=1, le=200, description="1ページあたりの件数")
    search_summary: str | None = Field(
        default=None, description="自然言語検索時の解釈説明（バナー表示用）"
    )
    extracted_filters: SearchConditionSchema | None = Field(
        default=None, description="自然言語検索時に抽出された条件"
    )
