"""ダッシュボード KPI エンドポイント."""

from fastapi import APIRouter, Depends
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user
from app.api.v1.schemas.auth import DashboardKpiResponse
from app.core.dependencies import get_db
from app.models.company import QualitativeSignal
from app.models.screening import ScreeningRun, ScoringResult
from app.models.user import User

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get("/kpi", response_model=DashboardKpiResponse)
async def get_dashboard_kpi(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DashboardKpiResponse:
    """KPI 集計（is_current=True のスクリーニング結果から集計）."""
    # is_current=True かつ success の run_id を取得
    run_stmt = (
        select(ScreeningRun.id)
        .where(
            and_(
                ScreeningRun.is_current == True,  # noqa: E712
                ScreeningRun.status == "success",
            )
        )
        .limit(1)
    )
    run_result = await db.execute(run_stmt)
    current_run_id = run_result.scalar_one_or_none()

    if current_run_id is None:
        # スクリーニング未実行: ゼロ値を返す
        return DashboardKpiResponse(
            total_companies=0,
            high_score_companies=0,
            avg_score=0.0,
            event_count=0,
        )

    # スコアの集計
    agg_stmt = select(
        func.count().label("total"),
        func.count().filter(ScoringResult.total_score >= 60).label("high_score"),
        func.coalesce(func.avg(ScoringResult.total_score), 0.0).label("avg"),
    ).where(ScoringResult.screening_run_id == current_run_id)

    agg_result = await db.execute(agg_stmt)
    row = agg_result.one()

    # QualitativeSignal の総件数（support のみ）
    event_stmt = select(func.count()).where(QualitativeSignal.stance == "support")
    event_result = await db.execute(event_stmt)
    event_count = event_result.scalar_one()

    return DashboardKpiResponse(
        total_companies=row.total,
        high_score_companies=row.high_score,
        avg_score=float(row.avg),
        event_count=event_count,
    )
