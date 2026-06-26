"""イベント Repository（直近イベントバナー用）."""

from datetime import date, timedelta

from sqlalchemy import and_, desc, select
from sqlalchemy.engine import Row
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company, Event
from app.models.screening import ScoringResult, ScreeningRun


class EventRepository:
    """Event の参照操作."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_recent(self, days: int = 7, limit: int = 10) -> list[Row]:
        """直近 ``days`` 日のイベントを occurred_at 降順で取得する。

        Event を Company と JOIN し、現行スクリーニング
        （is_current=True / status=success）の ScoringResult から
        event_score を LEFT JOIN して付与する。

        返り値: ``(Event, Company, event_score)`` の Row 一覧。
        """
        threshold = date.today() - timedelta(days=days)

        current_run_subq = (
            select(ScreeningRun.id)
            .where(
                and_(
                    ScreeningRun.is_current.is_(True),
                    ScreeningRun.status == "success",
                )
            )
            .limit(1)
            .scalar_subquery()
        )

        stmt = (
            select(Event, Company, ScoringResult.event_score)
            .join(Company, Event.company_id == Company.id)
            .outerjoin(
                ScoringResult,
                and_(
                    ScoringResult.company_id == Company.id,
                    ScoringResult.screening_run_id == current_run_subq,
                ),
            )
            .where(Event.occurred_at >= threshold)
            .order_by(desc(Event.occurred_at), desc(Event.created_at))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.all())
