"""企業・財務データ Repository."""

import uuid

from sqlalchemy import and_, desc, exists, func, select
from sqlalchemy.orm import selectinload

from app.models.company import Company, FinancialData, QualitativeSignal
from app.models.screening import ScoringResult, ScreeningRun
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

    async def find_current_run_id(self) -> uuid.UUID | None:
        """is_current=True かつ status=success の最新スクリーニング run_id を返す."""
        stmt = (
            select(ScreeningRun.id)
            .where(
                and_(
                    ScreeningRun.is_current.is_(True),
                    ScreeningRun.status == "success",
                )
            )
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def search_with_filters(
        self,
        run_id: uuid.UUID,
        *,
        conditions,
        sort_by: str = "total_score",
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict], int]:
        """SearchConditionSchema の条件で企業を絞り込む。

        対応条件:
        - company_name / securities_code: 完全一致
        - industry: 完全一致
        - unrealized_gain_min / max（FinancialData.unrealized_gain）
        - pbr_min / max（FinancialData.pbr）
        - structure_score_min（ScoringResult.structure_score）
        ※ region は対応するカラムが無いため適用しない。

        返り値: (items, total_count)
        """
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

        latest_fd_subq = (
            select(
                FinancialData.company_id,
                func.max(FinancialData.as_of_date).label("max_date"),
            )
            .group_by(FinancialData.company_id)
            .subquery()
        )

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
                FinancialData.pbr,
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

        # 完全一致条件
        if conditions.securities_code is not None:
            base_stmt = base_stmt.where(
                Company.securities_code == conditions.securities_code
            )
        if conditions.company_name is not None:
            base_stmt = base_stmt.where(Company.name == conditions.company_name)
        if conditions.industry is not None:
            base_stmt = base_stmt.where(Company.industry == conditions.industry)

        # 範囲条件（財務指標）
        if conditions.unrealized_gain_min is not None:
            base_stmt = base_stmt.where(
                FinancialData.unrealized_gain >= conditions.unrealized_gain_min
            )
        if conditions.unrealized_gain_max is not None:
            base_stmt = base_stmt.where(
                FinancialData.unrealized_gain <= conditions.unrealized_gain_max
            )
        if conditions.pbr_min is not None:
            base_stmt = base_stmt.where(FinancialData.pbr >= conditions.pbr_min)
        if conditions.pbr_max is not None:
            base_stmt = base_stmt.where(FinancialData.pbr <= conditions.pbr_max)

        # スコア条件
        if conditions.structure_score_min is not None:
            base_stmt = base_stmt.where(
                ScoringResult.structure_score >= conditions.structure_score_min
            )

        # 総件数
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
