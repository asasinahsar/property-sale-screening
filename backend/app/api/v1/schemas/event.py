"""イベント関連スキーマ（Pydantic v2 DTO）."""

import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class RecentEventSchema(BaseModel):
    """直近イベントバナーの 1 エントリ."""

    model_config = ConfigDict(from_attributes=True)

    company_id: uuid.UUID = Field(..., description="企業ID")
    securities_code: str = Field(
        ..., min_length=1, max_length=10, description="証券コード"
    )
    company_name: str = Field(..., min_length=1, max_length=255, description="企業名")
    event_type: str = Field(
        ..., description="イベント種別（new_disclosure / large_shareholding）"
    )
    occurred_at: date = Field(..., description="イベント発生日")
    event_score: float | None = Field(
        default=None, description="現行スクリーニングのイベントスコア（0–100）"
    )
