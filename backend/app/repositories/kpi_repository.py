"""効果検証 KPI スナップショット・工数ログ Repository."""

from datetime import date

from sqlalchemy import and_, desc, func, select

from app.models.kpi import KpiSnapshot, WorkLog
from app.repositories.base import BaseRepository


class KpiSnapshotRepository(BaseRepository[KpiSnapshot]):
    """KpiSnapshot の取得・作成操作."""

    def __init__(self, session):
        super().__init__(session, KpiSnapshot)

    async def get_latest(self) -> KpiSnapshot | None:
        """最新（created_at 降順）のスナップショットを 1 件取得."""
        stmt = select(KpiSnapshot).order_by(desc(KpiSnapshot.created_at)).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_period(
        self,
        period_from: date | None = None,
        period_to: date | None = None,
    ) -> list[KpiSnapshot]:
        """期間でフィルタしてスナップショットを昇順で取得.

        period_from/period_to が指定された場合は
        period_from >= ? AND period_to <= ? で絞り込む。
        未指定の場合は全件を期間昇順で返す。
        """
        stmt = select(KpiSnapshot)
        if period_from is not None:
            stmt = stmt.where(KpiSnapshot.period_from >= period_from)
        if period_to is not None:
            stmt = stmt.where(KpiSnapshot.period_to <= period_to)
        stmt = stmt.order_by(KpiSnapshot.period_from, KpiSnapshot.created_at)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class WorkLogRepository(BaseRepository[WorkLog]):
    """WorkLog の CRUD + 集計操作."""

    def __init__(self, session):
        super().__init__(session, WorkLog)

    async def list_by_range(
        self,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[WorkLog]:
        """logged_on の範囲でフィルタして工数ログを降順で取得."""
        stmt = select(WorkLog)
        if date_from is not None:
            stmt = stmt.where(WorkLog.logged_on >= date_from)
        if date_to is not None:
            stmt = stmt.where(WorkLog.logged_on <= date_to)
        stmt = stmt.order_by(desc(WorkLog.logged_on), desc(WorkLog.created_at))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def sum_duration(
        self,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> int:
        """logged_on の範囲内の duration_min 合計を返す."""
        stmt = select(func.coalesce(func.sum(WorkLog.duration_min), 0))
        if date_from is not None:
            stmt = stmt.where(WorkLog.logged_on >= date_from)
        if date_to is not None:
            stmt = stmt.where(WorkLog.logged_on <= date_to)
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def sum_duration_between(self, period_from: date, period_to: date) -> int:
        """期間内（両端含む）の工数合計を返す（スナップショット生成用）."""
        stmt = select(func.coalesce(func.sum(WorkLog.duration_min), 0)).where(
            and_(
                WorkLog.logged_on >= period_from,
                WorkLog.logged_on <= period_to,
            )
        )
        result = await self.session.execute(stmt)
        return int(result.scalar_one())
