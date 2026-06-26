"""ロングリスト管理・承認フロー＆エクスポート関連スキーマ（Pydantic v2 DTO）."""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

LonglistStatusLiteral = Literal["candidate", "approved", "rejected"]


# ---------------------------------------------------------------------------
# ロングリスト項目（レスポンス）
# ---------------------------------------------------------------------------


class LonglistItemSchema(BaseModel):
    """ロングリスト一覧の1項目（P003 ロングリスト画面用）."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., description="ロングリスト項目ID")
    company_id: uuid.UUID = Field(..., description="企業ID")
    securities_code: str = Field(..., description="証券コード")
    name: str = Field(..., description="企業名")
    industry: str = Field(..., description="業種")
    total_score: float | None = Field(default=None, description="総合スコア")
    structure_score: float | None = Field(default=None, description="構造スコア")
    event_score: float | None = Field(default=None, description="イベントスコア")
    unrealized_gain: float | None = Field(default=None, description="含み益（億円）")
    status: LonglistStatusLiteral = Field(..., description="ステータス")
    reason_memo: str | None = Field(default=None, description="選定理由メモ")
    created_by: uuid.UUID = Field(..., description="登録者ID")
    created_at: datetime = Field(..., description="登録日時")
    approved_by: uuid.UUID | None = Field(default=None, description="承認者ID")
    approved_at: datetime | None = Field(default=None, description="承認/却下日時")


class LonglistListResponse(BaseModel):
    """ロングリスト一覧レスポンス."""

    items: list[LonglistItemSchema] = Field(
        default_factory=list, description="ロングリスト項目一覧"
    )
    total: int = Field(..., ge=0, description="総件数")


# ---------------------------------------------------------------------------
# リクエスト
# ---------------------------------------------------------------------------


class LonglistCreateRequest(BaseModel):
    """ロングリスト追加リクエスト."""

    company_id: uuid.UUID = Field(..., description="追加する企業ID")


class LonglistUpdateRequest(BaseModel):
    """ロングリストメモ・ステータス更新リクエスト."""

    reason_memo: str | None = Field(
        default=None, max_length=500, description="選定理由メモ（最大500文字）"
    )
    status: LonglistStatusLiteral | None = Field(default=None, description="ステータス")


class LonglistApprovalRequest(BaseModel):
    """ロングリスト承認/却下リクエスト（manager のみ）."""

    action: Literal["approve", "reject"] = Field(
        ..., description="承認(approve) または 却下(reject)"
    )
    reason_memo: str | None = Field(
        default=None, max_length=500, description="承認/却下理由メモ（最大500文字）"
    )


# ---------------------------------------------------------------------------
# エクスポート
# ---------------------------------------------------------------------------


class LonglistExportResponse(BaseModel):
    """ロングリスト CSV エクスポート開始レスポンス（202 Accepted）."""

    model_config = ConfigDict(from_attributes=True)

    file_id: uuid.UUID = Field(..., description="生成ファイルID")
    status: Literal["pending", "processing", "completed", "failed"] = Field(
        ..., description="生成ステータス"
    )
    download_url: str | None = Field(
        default=None, description="ダウンロードURL（completed 時のみ設定）"
    )
    created_at: datetime = Field(..., description="生成リクエスト日時")
