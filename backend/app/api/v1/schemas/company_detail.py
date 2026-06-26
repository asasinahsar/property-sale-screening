"""企業詳細・根拠レポート関連スキーマ（Pydantic v2 DTO）."""

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.api.v1.schemas.scoring import (
    ConfidenceLevelEnum,
    SignalTypeEnum,
    StanceEnum,
)


# ---------------------------------------------------------------------------
# ドキュメントサマリー
# ---------------------------------------------------------------------------


class DocumentSummarySchema(BaseModel):
    """ドキュメントの概要情報."""

    model_config = ConfigDict(from_attributes=True)

    document_id: uuid.UUID = Field(..., description="ドキュメントID")
    document_type: str = Field(
        ...,
        description="ドキュメント種別（yuho/mid_term_plan/timely_disclosure/large_shareholding）",
    )
    disclosed_at: date = Field(..., description="開示日")
    source_url: str = Field(..., description="ソースURL")


# ---------------------------------------------------------------------------
# 定性シグナル詳細
# ---------------------------------------------------------------------------


class QualitativeSignalDetailSchema(BaseModel):
    """定性シグナルの詳細情報（根拠レポート表示用）."""

    model_config = ConfigDict(from_attributes=True)

    signal_id: uuid.UUID = Field(..., description="シグナルID")
    signal_type: SignalTypeEnum = Field(..., description="シグナル種別")
    stance: StanceEnum = Field(..., description="スタンス（support/counter）")
    strength: float | None = Field(
        default=None, ge=0.0, le=1.0, description="シグナル強度（0.0–1.0）"
    )
    quote_text: str = Field(..., description="根拠となる引用テキスト")
    source_page: int = Field(..., ge=1, description="引用元ページ番号")
    document: DocumentSummarySchema = Field(..., description="引用元ドキュメント情報")


# ---------------------------------------------------------------------------
# 財務データ詳細
# ---------------------------------------------------------------------------


class FinancialDataDetailSchema(BaseModel):
    """財務データの詳細情報（企業詳細画面表示用）."""

    model_config = ConfigDict(from_attributes=True)

    as_of_date: date = Field(..., description="財務データ基準日")
    revenue: float | None = Field(default=None, description="売上高（億円）")
    pbr: float | None = Field(default=None, description="PBR（株価純資産倍率）")
    adjusted_pbr: float | None = Field(default=None, description="修正PBR")
    equity_ratio: float | None = Field(
        default=None, ge=0.0, le=1.0, description="自己資本比率（0.0–1.0）"
    )
    re_market_value: float | None = Field(
        default=None, description="不動産時価（億円）"
    )
    re_book_value: float | None = Field(default=None, description="不動産簿価（億円）")
    unrealized_gain: float | None = Field(default=None, description="含み益（億円）")
    unrealized_gain_ratio: float | None = Field(
        default=None, description="含み益倍率（含み益/時価総額）"
    )
    roic: float | None = Field(default=None, description="ROIC")
    wacc: float | None = Field(default=None, description="WACC")
    stock_price: float | None = Field(default=None, description="株価（円）")

    @computed_field  # type: ignore[misc]
    @property
    def roic_wacc_gap(self) -> float | None:
        """ROIC - WACC のギャップ。どちらかが None の場合は None を返す."""
        if self.roic is None or self.wacc is None:
            return None
        return self.roic - self.wacc


# ---------------------------------------------------------------------------
# スコア内訳詳細
# ---------------------------------------------------------------------------


class ScoreBreakdownDetailSchema(BaseModel):
    """スコア内訳の詳細情報."""

    model_config = ConfigDict(from_attributes=True)

    structure_score: float = Field(
        ..., ge=0.0, le=100.0, description="構造スコア（0–100）"
    )
    event_score: float = Field(
        ..., ge=0.0, le=100.0, description="イベントスコア（0–100）"
    )
    total_score: float = Field(..., ge=0.0, description="統合総合スコア")
    event_boost: float | None = Field(
        default=None, ge=1.0, le=2.0, description="イベントブースト係数（1.0–2.0）"
    )
    confidence: ConfidenceLevelEnum = Field(..., description="信頼度レベル")
    ai_judgment: str | None = Field(default=None, description="AIによる判定コメント")
    judgment_refs: dict | None = Field(
        default=None,
        description='判定根拠の参照情報 e.g. {"signal_ids": [...], "metric_ids": [...]}',
    )
    score_breakdown: dict | None = Field(
        default=None,
        description='スコア内訳 e.g. {"structure": ..., "event": ..., "boost": ...}',
    )


# ---------------------------------------------------------------------------
# 企業詳細（メインレスポンス）
# ---------------------------------------------------------------------------


class CompanyDetailSchema(BaseModel):
    """企業詳細レスポンス（P002 企業詳細画面用）."""

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
    scoring: ScoreBreakdownDetailSchema | None = Field(
        default=None,
        description="最新スコア内訳。スコア未実行の場合は None",
    )
    financial: FinancialDataDetailSchema | None = Field(
        default=None,
        description="最新財務データ。データなしの場合は None",
    )
    signals_support: list[QualitativeSignalDetailSchema] = Field(
        default_factory=list,
        description="支持シグナル一覧（stance=support）",
    )
    signals_counter: list[QualitativeSignalDetailSchema] = Field(
        default_factory=list,
        description="反対シグナル一覧（stance=counter）",
    )


# ---------------------------------------------------------------------------
# レポート生成リクエスト / レスポンス
# ---------------------------------------------------------------------------


class ReportGenerateRequest(BaseModel):
    """根拠レポート生成リクエスト."""

    format: Literal["pdf"] = Field(
        default="pdf", description="出力フォーマット（現状 pdf のみ対応）"
    )


class ReportGenerateResponse(BaseModel):
    """根拠レポート生成開始レスポンス."""

    model_config = ConfigDict(from_attributes=True)

    file_id: uuid.UUID = Field(..., description="生成ファイルID")
    status: Literal["pending", "processing", "completed", "failed"] = Field(
        ..., description="生成ステータス"
    )
    download_url: str | None = Field(
        default=None, description="ダウンロードURL（completed 時のみ設定）"
    )
    created_at: datetime = Field(..., description="生成リクエスト日時")


class FileStatusResponse(BaseModel):
    """ファイル生成ステータス取得レスポンス."""

    model_config = ConfigDict(from_attributes=True)

    file_id: uuid.UUID = Field(..., description="生成ファイルID")
    status: Literal["pending", "processing", "completed", "failed"] = Field(
        ..., description="生成ステータス"
    )
    download_url: str | None = Field(
        default=None, description="ダウンロードURL（completed 時のみ設定）"
    )
    format: str = Field(..., description="ファイルフォーマット（例: pdf）")
    created_at: datetime = Field(..., description="生成リクエスト日時")
