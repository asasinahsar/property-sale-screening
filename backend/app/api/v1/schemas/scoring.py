"""スコアリングパイプライン関連スキーマ（Pydantic v2 DTO）."""

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class SignalTypeEnum(str, Enum):
    """定性シグナルの種別."""

    ACTIVIST_PROPOSAL = "activist_proposal"
    CAPITAL_EFFICIENCY_TARGET = "capital_efficiency_target"
    SALE_SUGGESTION = "sale_suggestion"
    OTHER = "other"


class StanceEnum(str, Enum):
    """定性シグナルのスタンス."""

    SUPPORT = "support"
    COUNTER = "counter"


class ConfidenceLevelEnum(str, Enum):
    """統合スコアの信頼度レベル."""

    HIGH = "high"
    MID = "mid"
    LOW = "low"


class RunStatusEnum(str, Enum):
    """スクリーニング実行ステータス."""

    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# 構造スコア関連
# ---------------------------------------------------------------------------


class FinancialDataInputSchema(BaseModel):
    """構造スコア算出のための財務データ入力."""

    company_id: uuid.UUID = Field(..., description="企業ID")
    pbr: float | None = Field(default=None, description="PBR（株価純資産倍率）")
    adjusted_pbr: float | None = Field(default=None, description="修正PBR")
    equity_ratio: float | None = Field(
        default=None, ge=0.0, le=1.0, description="自己資本比率（0.0–1.0）"
    )
    unrealized_gain: float | None = Field(default=None, description="含み益（億円）")
    unrealized_gain_ratio: float | None = Field(
        default=None, description="含み益倍率（含み益/時価総額）"
    )
    roic: float | None = Field(default=None, description="ROIC")
    wacc: float | None = Field(default=None, description="WACC")
    industry: str = Field(
        ..., min_length=1, max_length=100, description="業種（z-score正規化の単位）"
    )


class StructureScoreBreakdownSchema(BaseModel):
    """構造スコアの寄与内訳."""

    pbr_contribution: float = Field(
        ..., ge=0.0, le=1.0, description="PBRの寄与（0.0–1.0）"
    )
    equity_ratio_contribution: float = Field(
        ..., ge=0.0, le=1.0, description="自己資本比率の寄与（0.0–1.0）"
    )
    unrealized_gain_contribution: float = Field(
        ..., ge=0.0, le=1.0, description="含み益の寄与（0.0–1.0）"
    )
    roic_wacc_contribution: float = Field(
        ..., ge=0.0, le=1.0, description="ROIC/WACC比の寄与（0.0–1.0）"
    )


class StructureScoreOutputSchema(BaseModel):
    """構造スコアの算出結果."""

    model_config = ConfigDict(from_attributes=True)

    company_id: uuid.UUID = Field(..., description="企業ID")
    structure_score: float = Field(
        ..., ge=0.0, le=100.0, description="構造スコア（0–100）"
    )
    breakdown: StructureScoreBreakdownSchema = Field(..., description="スコア寄与内訳")


# ---------------------------------------------------------------------------
# 定性シグナル関連（LLM Agent 用）
# ---------------------------------------------------------------------------


class SignalExtractionRequestSchema(BaseModel):
    """定性シグナル抽出リクエスト（LLM Agent への入力）."""

    document_id: uuid.UUID = Field(..., description="対象ドキュメントID")
    document_text: str = Field(
        ..., min_length=1, description="抽出対象のドキュメント本文テキスト"
    )
    company_name: str = Field(..., min_length=1, max_length=255, description="企業名")


class ExtractedSignalSchema(BaseModel):
    """LLM Agent が抽出した1件の定性シグナル."""

    signal_type: SignalTypeEnum = Field(..., description="シグナル種別")
    stance: StanceEnum = Field(..., description="スタンス（support/counter）")
    strength: float = Field(..., ge=0.0, le=1.0, description="シグナル強度（0.0–1.0）")
    quote_text: str = Field(..., min_length=1, description="根拠となる引用テキスト")
    source_page: int = Field(..., ge=1, description="引用元ページ番号")


class SignalExtractionResponseSchema(BaseModel):
    """LLM Agent による定性シグナル抽出結果."""

    document_id: uuid.UUID | None = Field(
        default=None, description="抽出元ドキュメントID"
    )
    signals: list[ExtractedSignalSchema] = Field(
        default_factory=list, description="抽出されたシグナル一覧"
    )
    summary: str = Field(..., min_length=1, description="全シグナルの要約文")


# ---------------------------------------------------------------------------
# イベントスコア関連
# ---------------------------------------------------------------------------


class QualitativeSignalInputSchema(BaseModel):
    """イベントスコア算出のための定性シグナル入力."""

    signal_type: SignalTypeEnum = Field(..., description="シグナル種別")
    stance: StanceEnum = Field(..., description="スタンス")
    strength: float = Field(..., ge=0.0, le=1.0, description="シグナル強度（0.0–1.0）")
    recency_days: int | None = Field(
        default=None, ge=0, description="シグナルの新しさ（日数、小さいほど新しい）"
    )


class EventScoringInputSchema(BaseModel):
    """イベントスコア算出リクエスト."""

    company_id: uuid.UUID = Field(..., description="企業ID")
    signals: list[QualitativeSignalInputSchema] = Field(
        ..., min_length=0, description="定性シグナル一覧"
    )


class EventScoreOutputSchema(BaseModel):
    """イベントスコアの算出結果."""

    model_config = ConfigDict(from_attributes=True)

    company_id: uuid.UUID = Field(..., description="企業ID")
    event_score: float = Field(
        ..., ge=0.0, le=100.0, description="イベントスコア（0–100）"
    )
    event_boost: float = Field(
        ..., ge=1.0, le=2.0, description="イベントブースト係数（1.0–2.0）"
    )


# ---------------------------------------------------------------------------
# 統合スコア関連
# ---------------------------------------------------------------------------


class IntegratedScoringInputSchema(BaseModel):
    """統合スコア算出リクエスト."""

    company_id: uuid.UUID = Field(..., description="企業ID")
    structure_score: float = Field(
        ..., ge=0.0, le=100.0, description="構造スコア（0–100）"
    )
    event_score: float = Field(
        ..., ge=0.0, le=100.0, description="イベントスコア（0–100）"
    )
    event_boost: float = Field(
        ..., ge=1.0, le=2.0, description="イベントブースト係数（1.0–2.0）"
    )


class IntegratedScoringOutputSchema(BaseModel):
    """統合スコアの算出結果."""

    model_config = ConfigDict(from_attributes=True)

    company_id: uuid.UUID = Field(..., description="企業ID")
    total_score: float = Field(..., ge=0.0, description="統合総合スコア")
    confidence: ConfidenceLevelEnum = Field(..., description="信頼度レベル")
    ai_judgment: str | None = Field(default=None, description="AIによる判定コメント")
    judgment_refs: dict | None = Field(
        default=None,
        description='判定根拠の参照情報 e.g. {"signal_ids": [...], "metric_ids": [...]}',
    )
    score_breakdown: dict = Field(
        ...,
        description='スコア内訳 e.g. {"structure": ..., "event": ..., "boost": ...}',
    )


# ---------------------------------------------------------------------------
# スクリーニング実行・API 関連
# ---------------------------------------------------------------------------


class ScreeningRunResponse(BaseModel):
    """スクリーニング実行状態レスポンス."""

    model_config = ConfigDict(from_attributes=True)

    run_id: uuid.UUID = Field(..., description="スクリーニング実行ID")
    status: RunStatusEnum = Field(..., description="実行ステータス")
    started_at: datetime = Field(..., description="開始日時")
    finished_at: datetime | None = Field(default=None, description="完了日時")
    progress: int = Field(..., ge=0, le=100, description="進捗率（0–100 %）")


class ScreeningTriggerResponse(BaseModel):
    """スクリーニング起動レスポンス."""

    run_id: uuid.UUID = Field(..., description="発行されたスクリーニング実行ID")
    status: RunStatusEnum = Field(
        default=RunStatusEnum.RUNNING,
        description="起動直後のステータス（常に running）",
    )
    message: str = Field(..., min_length=1, description="起動確認メッセージ")


# ---------------------------------------------------------------------------
# 企業ランキング関連
# ---------------------------------------------------------------------------


class CompanyRankingItemSchema(BaseModel):
    """企業ランキング一覧の1エントリ."""

    model_config = ConfigDict(from_attributes=True)

    company_id: uuid.UUID = Field(..., description="企業ID")
    securities_code: str = Field(
        ..., min_length=1, max_length=10, description="証券コード"
    )
    name: str = Field(..., min_length=1, max_length=255, description="企業名")
    industry: str = Field(..., min_length=1, max_length=100, description="業種")
    market_cap: float | None = Field(
        default=None, ge=0.0, description="時価総額（億円）"
    )
    total_score: float = Field(..., ge=0.0, description="統合総合スコア")
    structure_score: float = Field(
        ..., ge=0.0, le=100.0, description="構造スコア（0–100）"
    )
    event_score: float = Field(
        ..., ge=0.0, le=100.0, description="イベントスコア（0–100）"
    )
    event_boost: float | None = Field(
        default=None, ge=1.0, le=2.0, description="イベントブースト係数"
    )
    confidence: ConfidenceLevelEnum = Field(..., description="信頼度レベル")
    unrealized_gain: float | None = Field(default=None, description="含み益（億円）")
    pbr: float | None = Field(default=None, description="PBR（株価純資産倍率）")
    has_event: bool = Field(..., description="イベントシグナルが1件以上あるか")


class CompanyListResponse(BaseModel):
    """企業ランキング一覧レスポンス（ページネーション付き）."""

    items: list[CompanyRankingItemSchema] = Field(
        default_factory=list, description="企業ランキング一覧"
    )
    total: int = Field(..., ge=0, description="総件数")
    page: int = Field(..., ge=1, description="現在ページ番号（1始まり）")
    page_size: int = Field(..., ge=1, le=200, description="1ページあたりの件数")
