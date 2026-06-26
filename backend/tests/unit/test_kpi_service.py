"""KpiService のユニットテスト.

工数集計とスナップショット生成の導出計算を実 DB（シードデータ）で検証する。
"""

import uuid
from datetime import date, datetime, timezone

import pytest
from sqlalchemy import delete, select

from app.core.database import AsyncSessionLocal
from app.models.company import Company
from app.models.kpi import KpiSnapshot, WorkLog
from app.models.screening import ScoringResult, ScreeningRun
from app.services.kpi_service import KpiService


@pytest.fixture
async def analyst_id():
    """シード済み analyst ユーザーID を取得（FK 用）."""
    from app.repositories.user_repository import UserRepository

    async with AsyncSessionLocal() as session:
        repo = UserRepository(session)
        user = await repo.get_by_email("analyst@example.com")
        if user is None:
            pytest.skip("シード analyst ユーザーが存在しないためスキップ")
        return user.id


@pytest.fixture
async def universe_companies():
    """シード済みの is_universe=True 企業を最大 2 件取得（存在しなければ skip）."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Company).where(Company.is_universe.is_(True)).limit(2)
        )
        companies = list(result.scalars().all())
        if len(companies) < 1:
            pytest.skip("シード universe 企業が存在しないためスキップ")
        return [c.id for c in companies]


# ---------------------------------------------------------------------------
# 工数ログ
# ---------------------------------------------------------------------------


class TestWorkLogs:
    async def test_add_and_list(self, analyst_id):
        service_session = AsyncSessionLocal()
        async with service_session as session:
            await session.execute(delete(WorkLog))
            await session.commit()
            service = KpiService(session)
            await service.add_work_log(
                user_id=analyst_id,
                task_type="primary_screening",
                duration_min=120,
                logged_on=date(2025, 6, 26),
            )
            await service.add_work_log(
                user_id=analyst_id,
                task_type="report",
                duration_min=30,
                logged_on=date(2025, 6, 26),
            )
            items, total = await service.list_work_logs()
            assert total == 150
            assert len(items) == 2
            await session.execute(delete(WorkLog))
            await session.commit()


# ---------------------------------------------------------------------------
# スナップショット生成
# ---------------------------------------------------------------------------


class TestGenerateSnapshot:
    async def test_generate_snapshot_derives_metrics(
        self, analyst_id, universe_companies
    ):
        run_id = uuid.uuid4()
        async with AsyncSessionLocal() as session:
            # クリーンアップ
            await session.execute(delete(WorkLog))
            await session.commit()

            # スクリーニング実行を作成
            run = ScreeningRun(
                id=run_id,
                triggered_by=analyst_id,
                status="success",
                is_current=True,
                started_at=datetime(2025, 6, 26, 9, 0, tzinfo=timezone.utc),
                finished_at=datetime(2025, 6, 26, 9, 5, tzinfo=timezone.utc),
            )
            session.add(run)

            # スコアリング結果を作成
            for cid in universe_companies:
                session.add(
                    ScoringResult(
                        id=uuid.uuid4(),
                        screening_run_id=run_id,
                        company_id=cid,
                        structure_score=60.0,
                        event_score=10.0,
                        total_score=70.0,
                        confidence="high",
                    )
                )

            # 期間内の工数ログを作成
            session.add(
                WorkLog(
                    id=uuid.uuid4(),
                    user_id=analyst_id,
                    task_type="primary_screening",
                    duration_min=600,
                    logged_on=date(2025, 6, 10),
                    created_at=datetime.now(timezone.utc),
                )
            )
            await session.commit()

            service = KpiService(session)
            snapshot = await service.generate_snapshot(run_id)

            assert snapshot.id is not None
            assert snapshot.period_from == date(2025, 6, 1)
            assert snapshot.period_to == date(2025, 6, 26)
            # 全スコアリング結果の structure_score が 60 → 平均 60
            assert float(snapshot.avg_structure_score) == pytest.approx(60.0, abs=0.01)
            # reproducibility は暫定で avg_structure_score と一致
            assert float(snapshot.reproducibility_score) == pytest.approx(
                float(snapshot.avg_structure_score), abs=0.01
            )
            # 工数 600 分 → 削減率 = (1 - 600/30000)*100 = 98.0
            assert float(snapshot.workload_reduction_rate) == pytest.approx(
                98.0, abs=0.01
            )
            assert snapshot.total_workload_min == 600
            # universe_coverage は 0–100 の範囲
            assert 0.0 <= float(snapshot.universe_coverage) <= 100.0
            # traceability_rate は 0–100 の範囲
            assert 0.0 <= float(snapshot.traceability_rate) <= 100.0

        # クリーンアップ
        async with AsyncSessionLocal() as session:
            await session.execute(
                delete(KpiSnapshot).where(KpiSnapshot.id == snapshot.id)
            )
            await session.execute(
                delete(ScoringResult).where(ScoringResult.screening_run_id == run_id)
            )
            await session.execute(delete(WorkLog))
            await session.execute(delete(ScreeningRun).where(ScreeningRun.id == run_id))
            await session.commit()
