"""企業・財務データ Repository."""

import uuid

from sqlalchemy import and_, desc, exists, func, select
from sqlalchemy.orm import selectinload

from app.models.company import Company, FinancialData, QualitativeSignal
from app.models.screening import ScoringResult
from app.repositories.base import BaseRepository


class CompanyRepository(BaseRepository[Company]):
    """Company の取得操作."""

    def __init__(self, session):
        super().__init__(session, Company)

    async def get_all_universe(self) -> list[Company]:
        """is_universe=True の全企業を取得（financial_data を eager load）."""
        stmt = (
            select(Company)
            .where(Company.is_universe.is_(True))
            .options(selectinload(Company.financial_data))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_companies_with_scores(
        self,
        run_id: uuid.UUID,
        industry: str | None = None,
        min_score: float | None = None,
        max_score: float | None = None,
        has_event: bool | None = None,
        sort_by: str = "total_score",
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict], int]:
        """指定 run_id のスコアと企業情報を JOIN して返す。

        返り値: (items, total_count)
        """
        # has_event のサブクエリ
        has_event_subq = (
            exists()
            .where(
                and_(
                    QualitativeSignal.company_id == Company.id,
                    QualitativeSignal.stance == "support",
                )
            )
            .correlate(Company)
        )

        # FinancialData のサブクエリ: 企業ごとに最新 as_of_date を取得
        latest_fd_subq = (
            select(
                FinancialData.company_id,
                func.max(FinancialData.as_of_date).label("max_date"),
            )
            .group_by(FinancialData.company_id)
            .subquery()
        )

        # ベースクエリ
        base_stmt = (
            select(
                Company.id.label("company_id"),
                Company.securities_code,
                Company.name,
                Company.industry,
                Company.market_cap,
                ScoringResult.total_score,
                ScoringResult.structure_score,
                ScoringResult.event_score,
                ScoringResult.event_boost,
                ScoringResult.confidence,
                FinancialData.unrealized_gain,
                has_event_subq.label("has_event"),
            )
            .join(
                ScoringResult,
                and_(
                    ScoringResult.company_id == Company.id,
                    ScoringResult.screening_run_id == run_id,
                ),
            )
            .outerjoin(
                latest_fd_subq,
                latest_fd_subq.c.company_id == Company.id,
            )
            .outerjoin(
                FinancialData,
                and_(
                    FinancialData.company_id == Company.id,
                    FinancialData.as_of_date == latest_fd_subq.c.max_date,
                ),
            )
        )

        # フィルタ条件
        if industry is not None:
            base_stmt = base_stmt.where(Company.industry == industry)
        if min_score is not None:
            base_stmt = base_stmt.where(ScoringResult.total_score >= min_score)
        if max_score is not None:
            base_stmt = base_stmt.where(ScoringResult.total_score <= max_score)
        if has_event is not None:
            base_stmt = base_stmt.where(has_event_subq == has_event)

        # 総件数を取得
        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        count_result = await self.session.execute(count_stmt)
        total_count = count_result.scalar_one()

        # ソート
        sort_column_map = {
            "total_score": ScoringResult.total_score,
            "structure_score": ScoringResult.structure_score,
            "event_score": ScoringResult.event_score,
        }
        sort_col = sort_column_map.get(sort_by, ScoringResult.total_score)
        base_stmt = base_stmt.order_by(desc(sort_col))

        # ページネーション
        offset = (page - 1) * page_size
        base_stmt = base_stmt.offset(offset).limit(page_size)

        result = await self.session.execute(base_stmt)
        rows = result.mappings().all()

        items = [dict(row) for row in rows]
        return items, total_count


class FinancialDataRepository(BaseRepository[FinancialData]):
    """FinancialData の取得操作."""

    def __init__(self, session):
        super().__init__(session, FinancialData)

    async def get_latest_by_company(
        self, company_id: uuid.UUID
    ) -> FinancialData | None:
        """企業の最新財務データを取得（as_of_date 降順で1件）."""
        stmt = (
            select(FinancialData)
            .where(FinancialData.company_id == company_id)
            .order_by(desc(FinancialData.as_of_date))
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_latest(self) -> list[FinancialData]:
        """全企業の最新財務データを取得（as_of_date ごとに最新のみ）."""
        # 企業ごとの最新 as_of_date サブクエリ
        latest_dates_subq = (
            select(
                FinancialData.company_id,
                func.max(FinancialData.as_of_date).label("max_date"),
            )
            .group_by(FinancialData.company_id)
            .subquery()
        )

        stmt = select(FinancialData).join(
            latest_dates_subq,
            and_(
                FinancialData.company_id == latest_dates_subq.c.company_id,
                FinancialData.as_of_date == latest_dates_subq.c.max_date,
            ),
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
