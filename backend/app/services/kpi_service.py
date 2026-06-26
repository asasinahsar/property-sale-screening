"""効果検証 KPI サービス（ビジネスロジック層）.

- 工数ログの記録・集計
- スクリーニング実行完了時の KPI スナップショット生成
"""

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import and_, distinct, exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company, QualitativeSignal
from app.models.kpi import KpiSnapshot, WorkLog
from app.models.screening import ScreeningRun, ScoringResult
from app.repositories.kpi_repository import KpiSnapshotRepository, WorkLogRepository

# 工数削減率の基準（人手での想定総工数: 500 時間 = 500 * 60 分）
_BASELINE_WORKLOAD_MIN = 500 * 60


class KpiService:
    """効果検証 KPI のビジネスロジック."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.snapshot_repo = KpiSnapshotRepository(session)
        self.work_log_repo = WorkLogRepository(session)

    # ------------------------------------------------------------------
    # 効果検証 KPI（読み取り）
    # ------------------------------------------------------------------

    async def get_effectiveness(
        self,
        period_from: date | None = None,
        period_to: date | None = None,
    ) -> tuple[list[KpiSnapshot], KpiSnapshot | None]:
        """期間内のスナップショット一覧と最新スナップショットを返す.

        period_from/period_to 未指定時は最新 1 件を latest として返す。
        """
        snapshots = await self.snapshot_repo.list_by_period(period_from, period_to)
        if period_from is None and period_to is None:
            latest = await self.snapshot_repo.get_latest()
        else:
            latest = snapshots[-1] if snapshots else None
        return snapshots, latest

    # ------------------------------------------------------------------
    # 工数ログ
    # ------------------------------------------------------------------

    async def add_work_log(
        self,
        user_id: uuid.UUID,
        task_type: str,
        duration_min: int,
        logged_on: date,
        screening_run_id: uuid.UUID | None = None,
        period_label: str | None = None,
    ) -> WorkLog:
        """工数ログを記録する."""
        work_log = WorkLog(
            id=uuid.uuid4(),
            user_id=user_id,
            task_type=task_type,
            duration_min=duration_min,
            screening_run_id=screening_run_id,
            period_label=period_label,
            logged_on=logged_on,
            created_at=datetime.now(timezone.utc),
        )
        return await self.work_log_repo.create(work_log)

    async def list_work_logs(
        self,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> tuple[list[WorkLog], int]:
        """工数ログ一覧と合計工数を返す."""
        items = await self.work_log_repo.list_by_range(date_from, date_to)
        total_min = await self.work_log_repo.sum_duration(date_from, date_to)
        return items, total_min

    # ------------------------------------------------------------------
    # KPI スナップショット生成（スクリーニング完了フック）
    # ------------------------------------------------------------------

    async def generate_snapshot(self, run_id: uuid.UUID) -> KpiSnapshot:
        """スクリーニング実行完了時に効果検証 KPI スナップショットを生成する.

        導出計算:
        - universe_coverage: is_universe=true 企業のうちスコアリング済み割合(%)
        - traceability_rate: scoring_results のうち定性シグナルに紐づくもの割合(%)
        - avg_structure_score: 全 scoring_results の structure_score 平均
        - reproducibility_score: 暫定 = avg_structure_score
        - total_workload_min: 期間内の work_logs.duration_min 合計
        - workload_reduction_rate: (1 - total / baseline) * 100
        """
        # スナップショット対象期間（実行完了月を集計対象とする）
        run = await self.session.get(ScreeningRun, run_id)
        finished = (
            run.finished_at if run and run.finished_at else None
        ) or datetime.now(timezone.utc)
        period_to = finished.date()
        period_from = period_to.replace(day=1)

        # universe_coverage --------------------------------------------------
        total_universe_stmt = select(func.count()).where(Company.is_universe.is_(True))
        total_universe = int(
            (await self.session.execute(total_universe_stmt)).scalar_one()
        )

        scored_universe_stmt = (
            select(func.count(distinct(ScoringResult.company_id)))
            .join(Company, Company.id == ScoringResult.company_id)
            .where(
                and_(
                    ScoringResult.screening_run_id == run_id,
                    Company.is_universe.is_(True),
                )
            )
        )
        scored_universe = int(
            (await self.session.execute(scored_universe_stmt)).scalar_one()
        )
        universe_coverage = (
            round(scored_universe / total_universe * 100, 2)
            if total_universe > 0
            else 0.0
        )

        # avg_structure_score & total count ---------------------------------
        agg_stmt = select(
            func.count().label("total"),
            func.coalesce(func.avg(ScoringResult.structure_score), 0.0).label("avg"),
        ).where(ScoringResult.screening_run_id == run_id)
        agg_row = (await self.session.execute(agg_stmt)).one()
        total_results = int(agg_row.total)
        avg_structure_score = round(float(agg_row.avg), 2)

        # traceability_rate -------------------------------------------------
        has_signal_subq = (
            exists()
            .where(QualitativeSignal.company_id == ScoringResult.company_id)
            .correlate(ScoringResult)
        )
        traceable_stmt = (
            select(func.count())
            .select_from(ScoringResult)
            .where(
                and_(
                    ScoringResult.screening_run_id == run_id,
                    has_signal_subq,
                )
            )
        )
        traceable = int((await self.session.execute(traceable_stmt)).scalar_one())
        traceability_rate = (
            round(traceable / total_results * 100, 2) if total_results > 0 else 0.0
        )

        # workload ----------------------------------------------------------
        total_workload_min = await self.work_log_repo.sum_duration_between(
            period_from, period_to
        )
        workload_reduction_rate = round(
            (1.0 - total_workload_min / _BASELINE_WORKLOAD_MIN) * 100, 2
        )

        snapshot = KpiSnapshot(
            id=uuid.uuid4(),
            period_from=period_from,
            period_to=period_to,
            universe_coverage=universe_coverage,
            traceability_rate=traceability_rate,
            avg_structure_score=avg_structure_score,
            reproducibility_score=avg_structure_score,
            total_workload_min=total_workload_min,
            workload_reduction_rate=workload_reduction_rate,
        )
        return await self.snapshot_repo.create(snapshot)
