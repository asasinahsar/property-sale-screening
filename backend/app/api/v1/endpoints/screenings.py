"""スクリーニング実行エンドポイント."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user
from app.api.v1.schemas.scoring import (
    RunStatusEnum,
    ScreeningRunResponse,
    ScreeningTriggerResponse,
)
from app.core.database import AsyncSessionLocal
from app.core.dependencies import get_db
from app.models.screening import ScreeningRun
from app.models.user import User

router = APIRouter(prefix="/api/v1/screenings", tags=["screenings"])


async def _run_scoring_pipeline(run_id: uuid.UUID) -> None:
    """スコアリングパイプライン実行（バックグラウンド）."""
    async with AsyncSessionLocal() as session:
        try:
            # 暫定: 実際のスコアリング処理の代わりにデモ用スリープ
            import asyncio

            await asyncio.sleep(3)

            # screening_run を success / is_current=True に更新
            stmt = select(ScreeningRun).where(ScreeningRun.id == run_id)
            result = await session.execute(stmt)
            run = result.scalar_one_or_none()

            if run is not None:
                run.status = "success"
                run.is_current = True
                run.finished_at = datetime.now(timezone.utc)
                await session.commit()

        except Exception:
            # エラー時は failed に更新
            try:
                async with AsyncSessionLocal() as err_session:
                    stmt = select(ScreeningRun).where(ScreeningRun.id == run_id)
                    result = await err_session.execute(stmt)
                    run = result.scalar_one_or_none()
                    if run is not None:
                        run.status = "failed"
                        run.finished_at = datetime.now(timezone.utc)
                        await err_session.commit()
            except Exception:
                pass


@router.post(
    "",
    response_model=ScreeningTriggerResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def trigger_screening(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ScreeningTriggerResponse:
    """スクリーニングを非同期で実行開始する（202 Accepted）."""
    run_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    run = ScreeningRun(
        id=run_id,
        triggered_by=current_user.id,
        status="running",
        is_current=False,
        started_at=now,
    )
    db.add(run)
    await db.commit()

    background_tasks.add_task(_run_scoring_pipeline, run_id)

    return ScreeningTriggerResponse(
        run_id=run_id,
        status=RunStatusEnum.RUNNING,
        message="Screening started. Use run_id to check status.",
    )


@router.get("/{run_id}", response_model=ScreeningRunResponse)
async def get_screening_status(
    run_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ScreeningRunResponse:
    """スクリーニング実行状態を取得する."""
    stmt = select(ScreeningRun).where(ScreeningRun.id == run_id)
    result = await db.execute(stmt)
    run = result.scalar_one_or_none()

    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Screening run not found",
        )

    progress_map = {"running": 50, "success": 100, "failed": 0}

    return ScreeningRunResponse(
        run_id=run.id,
        status=RunStatusEnum(run.status),
        started_at=run.started_at,
        finished_at=run.finished_at,
        progress=progress_map.get(run.status, 0),
    )
