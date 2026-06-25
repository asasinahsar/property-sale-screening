"""スクリーニング実行エンドポイント."""

import uuid
from datetime import date, datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user
from app.api.v1.schemas.scoring import (
    EventScoringInputSchema,
    FinancialDataInputSchema,
    IntegratedScoringInputSchema,
    QualitativeSignalInputSchema,
    RunStatusEnum,
    ScreeningRunResponse,
    ScreeningTriggerResponse,
    SignalTypeEnum,
    StanceEnum,
)
from app.core.database import AsyncSessionLocal
from app.core.dependencies import get_db
from app.models.company import QualitativeSignal
from app.models.screening import ScreeningRun, ScoringResult
from app.models.user import User
from app.repositories.company_repository import CompanyRepository, FinancialDataRepository
from app.repositories.screening_repository import (
    ScreeningRunRepository,
    ScoringResultRepository,
)
from app.services.event_scoring import EventScoringService
from app.services.integration_scoring import IntegrationScoringService
from app.services.structure_scoring import StructureScoringService

router = APIRouter(prefix="/api/v1/screenings", tags=["screenings"])


def _build_financial_input(company, fd) -> FinancialDataInputSchema:
    """Company + FinancialData から FinancialDataInputSchema を構築."""
    if fd is None:
        return FinancialDataInputSchema(
            company_id=company.id,
            industry=company.industry,
        )
    raw_equity = float(fd.equity_ratio) if fd.equity_ratio is not None else None
    # DBに%表記（例: 45.5）で入っている場合は小数（0.455）に変換
    if raw_equity is not None and raw_equity > 1.0:
        raw_equity = raw_equity / 100.0
    raw_equity = min(1.0, max(0.0, raw_equity)) if raw_equity is not None else None

    return FinancialDataInputSchema(
        company_id=company.id,
        pbr=float(fd.pbr) if fd.pbr is not None else None,
        adjusted_pbr=float(fd.adjusted_pbr) if fd.adjusted_pbr is not None else None,
        equity_ratio=raw_equity,
        unrealized_gain=float(fd.unrealized_gain) if fd.unrealized_gain is not None else None,
        unrealized_gain_ratio=float(fd.unrealized_gain_ratio) if fd.unrealized_gain_ratio is not None else None,
        roic=float(fd.roic) if fd.roic is not None else None,
        wacc=float(fd.wacc) if fd.wacc is not None else None,
        industry=company.industry,
    )


async def _run_scoring_pipeline(run_id: uuid.UUID) -> None:
    """スコアリングパイプライン実行（バックグラウンド）."""
    async with AsyncSessionLocal() as session:
        run_repo = ScreeningRunRepository(session)
        result_repo = ScoringResultRepository(session)
        company_repo = CompanyRepository(session)
        fd_repo = FinancialDataRepository(session)

        structure_svc = StructureScoringService()
        event_svc = EventScoringService()
        integration_svc = IntegrationScoringService()

        try:
            # 1. 対象企業（is_universe=True）を全取得
            companies = await company_repo.get_all_universe()
            if not companies:
                await run_repo.set_current(run_id)
                return

            # 2. 全企業の最新財務データをまとめて取得（N+1回避）
            all_fd = await fd_repo.get_all_latest()
            fd_by_company = {fd.company_id: fd for fd in all_fd}

            # 3. 全企業の財務入力を構築（業種内z-score用）
            all_fi_inputs = [
                _build_financial_input(c, fd_by_company.get(c.id))
                for c in companies
            ]
            # 業種別にグループ化
            peers_by_industry: dict[str, list[FinancialDataInputSchema]] = {}
            for fi in all_fi_inputs:
                peers_by_industry.setdefault(fi.industry, []).append(fi)

            # 4. 各企業の定性シグナルを取得
            from sqlalchemy import and_
            signal_stmt = select(QualitativeSignal).where(
                QualitativeSignal.company_id.in_([c.id for c in companies])
            )
            signal_result = await session.execute(signal_stmt)
            all_signals = signal_result.scalars().all()

            signals_by_company: dict[uuid.UUID, list[QualitativeSignal]] = {}
            for sig in all_signals:
                signals_by_company.setdefault(sig.company_id, []).append(sig)

            # 5. 各企業のスコアを算出
            scoring_results: list[ScoringResult] = []
            today = date.today()

            for company, fi_input in zip(companies, all_fi_inputs):
                peers = peers_by_industry.get(company.industry, [])

                # 構造スコア
                structure_out = structure_svc.calculate(fi_input, peers=peers if len(peers) > 1 else None)

                # イベントスコア（定性シグナルから）
                company_signals = signals_by_company.get(company.id, [])
                signal_inputs = []
                for sig in company_signals:
                    recency_days = None
                    if sig.recency is not None:
                        recency_days = (today - sig.recency).days
                    try:
                        signal_inputs.append(QualitativeSignalInputSchema(
                            signal_type=SignalTypeEnum(sig.signal_type),
                            stance=StanceEnum(sig.stance),
                            strength=float(sig.strength) if sig.strength is not None else 0.5,
                            recency_days=recency_days,
                        ))
                    except ValueError:
                        continue

                event_input = EventScoringInputSchema(
                    company_id=company.id,
                    signals=signal_inputs,
                )
                event_out = event_svc.calculate(event_input)

                # 統合スコア
                integrated_input = IntegratedScoringInputSchema(
                    company_id=company.id,
                    structure_score=structure_out.structure_score,
                    event_score=event_out.event_score,
                    event_boost=event_out.event_boost,
                )
                integrated_out = integration_svc.integrate(integrated_input)

                scoring_results.append(ScoringResult(
                    screening_run_id=run_id,
                    company_id=company.id,
                    structure_score=structure_out.structure_score,
                    event_score=event_out.event_score,
                    total_score=integrated_out.total_score,
                    event_boost=event_out.event_boost,
                    confidence=integrated_out.confidence.value,
                    ai_judgment=integrated_out.ai_judgment,
                    judgment_refs=integrated_out.judgment_refs,
                    score_breakdown=integrated_out.score_breakdown,
                ))

            # 6. 一括保存 → run を current に
            await result_repo.bulk_create(scoring_results)
            await run_repo.set_current(run_id)

        except Exception as e:
            try:
                await run_repo.mark_failed(run_id)
            except Exception:
                pass
            raise e


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
