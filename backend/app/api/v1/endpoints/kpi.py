"""効果検証ダッシュボード・KPI 計測エンドポイント."""

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user
from app.api.v1.schemas.kpi import (
    EffectivenessResponse,
    KpiSnapshotSchema,
    WorkLogCreateRequest,
    WorkLogListResponse,
    WorkLogSchema,
)
from app.core.dependencies import get_db
from app.models.user import User
from app.services.kpi_service import KpiService

router = APIRouter(prefix="/api/v1/kpi", tags=["kpi"])


@router.get("/effectiveness", response_model=EffectivenessResponse)
async def get_effectiveness(
    period_from: date | None = Query(default=None, description="集計期間（開始）"),
    period_to: date | None = Query(default=None, description="集計期間（終了）"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EffectivenessResponse:
    """効果検証 KPI スナップショットを取得する（読み取り専用）."""
    service = KpiService(db)
    snapshots, latest = await service.get_effectiveness(period_from, period_to)
    return EffectivenessResponse(
        snapshots=[KpiSnapshotSchema.model_validate(s) for s in snapshots],
        latest=KpiSnapshotSchema.model_validate(latest) if latest else None,
    )


@router.post("/work-logs", response_model=WorkLogSchema, status_code=201)
async def create_work_log(
    payload: WorkLogCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkLogSchema:
    """工数ログを記録する（JWT 認証必須）."""
    service = KpiService(db)
    work_log = await service.add_work_log(
        user_id=current_user.id,
        task_type=payload.task_type.value,
        duration_min=payload.duration_min,
        logged_on=payload.logged_on,
        screening_run_id=payload.screening_run_id,
        period_label=payload.period_label,
    )
    return WorkLogSchema.model_validate(work_log)


@router.get("/work-logs", response_model=WorkLogListResponse)
async def list_work_logs(
    from_: date | None = Query(default=None, alias="from", description="開始日"),
    to: date | None = Query(default=None, description="終了日"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkLogListResponse:
    """工数ログ一覧を取得する."""
    service = KpiService(db)
    items, total_min = await service.list_work_logs(from_, to)
    return WorkLogListResponse(
        items=[WorkLogSchema.model_validate(i) for i in items],
        total_min=total_min,
    )
