"""効果検証ダッシュボード・KPI 計測関連スキーマ（Pydantic v2 DTO）."""

import uuid
from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class TaskTypeEnum(str, Enum):
    """工数ログのタスク種別."""

    PRIMARY_SCREENING = "primary_screening"
    DEEP_DIVE = "deep_dive"
    REPORT = "report"
    OTHER = "other"


# ---------------------------------------------------------------------------
# KPI スナップショット
# ---------------------------------------------------------------------------


class KpiSnapshotSchema(BaseModel):
    """効果検証 KPI スナップショット（読み取り専用）."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., description="スナップショットID")
    period_from: date = Field(..., description="集計期間（開始）")
    period_to: date = Field(..., description="集計期間（終了）")
    universe_coverage: float | None = Field(
        default=None, description="ユニバースカバレッジ（%）"
    )
    traceability_rate: float | None = Field(
        default=None, description="トレース可能率（%）"
    )
    avg_structure_score: float | None = Field(
        default=None, description="平均構造スコア"
    )
    reproducibility_score: float | None = Field(
        default=None, description="再現性スコア"
    )
    total_workload_min: int | None = Field(default=None, description="総工数（分）")
    workload_reduction_rate: float | None = Field(
        default=None, description="工数削減率（%）"
    )
    created_at: datetime = Field(..., description="作成日時")


class EffectivenessResponse(BaseModel):
    """効果検証 KPI レスポンス（最新 + 推移）."""

    snapshots: list[KpiSnapshotSchema] = Field(
        default_factory=list, description="期間内の KPI スナップショット一覧（昇順）"
    )
    latest: KpiSnapshotSchema | None = Field(
        default=None, description="最新の KPI スナップショット"
    )


# ---------------------------------------------------------------------------
# 工数ログ
# ---------------------------------------------------------------------------


class WorkLogCreateRequest(BaseModel):
    """工数ログ記録リクエスト."""

    task_type: TaskTypeEnum = Field(..., description="タスク種別")
    duration_min: int = Field(..., gt=0, description="所要時間（分）")
    screening_run_id: uuid.UUID | None = Field(
        default=None, description="関連スクリーニング実行ID（任意）"
    )
    period_label: str | None = Field(
        default=None, max_length=255, description="期間ラベル（任意）"
    )
    logged_on: date = Field(..., description="記録対象日")


class WorkLogSchema(BaseModel):
    """工数ログ."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., description="工数ログID")
    user_id: uuid.UUID = Field(..., description="記録者ユーザーID")
    task_type: TaskTypeEnum = Field(..., description="タスク種別")
    duration_min: int = Field(..., description="所要時間（分）")
    screening_run_id: uuid.UUID | None = Field(
        default=None, description="関連スクリーニング実行ID"
    )
    period_label: str | None = Field(default=None, description="期間ラベル")
    logged_on: date = Field(..., description="記録対象日")
    created_at: datetime = Field(..., description="作成日時")


class WorkLogListResponse(BaseModel):
    """工数ログ一覧レスポンス."""

    items: list[WorkLogSchema] = Field(default_factory=list, description="工数ログ一覧")
    total_min: int = Field(default=0, description="合計工数（分）")
