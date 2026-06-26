"""LonglistRepository - ロングリストデータアクセス層."""

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company, FinancialData
from app.models.longlist import LonglistItem
from app.models.screening import ScreeningRun, ScoringResult


@dataclass
class LonglistRow:
    """ロングリスト一覧の1行（JOIN 結果）."""

    item: LonglistItem
    company: Company
    scoring: ScoringResult | None
    financial: FinancialData | None


class LonglistRepository:
    """longlist_items の CRUD とテーブル結合取得を担うリポジトリ."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_items(self) -> list[LonglistRow]:
        """ロングリスト項目を Company / ScoringResult / FinancialData と
        結合して全件取得する（created_at 降順）.
        """
        # 各企業の最新財務データ（as_of_date 最大）の company_id を相関サブクエリで判定
        latest_fin_subq = (
            select(func.max(FinancialData.as_of_date))
            .where(FinancialData.company_id == Company.id)
            .correlate(Company)
            .scalar_subquery()
        )

        stmt = (
            select(LonglistItem, Company, ScoringResult, FinancialData)
            .join(Company, LonglistItem.company_id == Company.id)
            .outerjoin(
                ScoringResult, ScoringResult.id == LonglistItem.scoring_result_id
            )
            .outerjoin(
                FinancialData,
                and_(
                    FinancialData.company_id == Company.id,
                    FinancialData.as_of_date == latest_fin_subq,
                ),
            )
            .order_by(desc(LonglistItem.created_at))
        )
        result = await self.session.execute(stmt)
        rows = result.all()
        return [
            LonglistRow(
                item=item, company=company, scoring=scoring, financial=financial
            )
            for item, company, scoring, financial in rows
        ]

    async def get_row_by_id(self, item_id: uuid.UUID) -> LonglistRow | None:
        """ID 指定で Company / ScoringResult / FinancialData を結合した1行を取得する."""
        latest_fin_subq = (
            select(func.max(FinancialData.as_of_date))
            .where(FinancialData.company_id == Company.id)
            .correlate(Company)
            .scalar_subquery()
        )
        stmt = (
            select(LonglistItem, Company, ScoringResult, FinancialData)
            .join(Company, LonglistItem.company_id == Company.id)
            .outerjoin(
                ScoringResult, ScoringResult.id == LonglistItem.scoring_result_id
            )
            .outerjoin(
                FinancialData,
                and_(
                    FinancialData.company_id == Company.id,
                    FinancialData.as_of_date == latest_fin_subq,
                ),
            )
            .where(LonglistItem.id == item_id)
        )
        result = await self.session.execute(stmt)
        row = result.first()
        if row is None:
            return None
        item, company, scoring, financial = row
        return LonglistRow(
            item=item, company=company, scoring=scoring, financial=financial
        )

    async def count(self) -> int:
        """ロングリスト項目の総件数を返す."""
        stmt = select(func.count()).select_from(LonglistItem)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_by_id(self, item_id: uuid.UUID) -> LonglistItem | None:
        """ID で1件取得する."""
        return await self.session.get(LonglistItem, item_id)

    async def get_by_company_id(self, company_id: uuid.UUID) -> LonglistItem | None:
        """company_id で1件取得する（重複チェック用）."""
        stmt = select(LonglistItem).where(LonglistItem.company_id == company_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_current_scoring_result_id(
        self, company_id: uuid.UUID
    ) -> uuid.UUID | None:
        """is_current=True かつ success のスクリーニング結果 ID を取得する."""
        stmt = (
            select(ScoringResult.id)
            .join(
                ScreeningRun,
                and_(
                    ScoringResult.screening_run_id == ScreeningRun.id,
                    ScreeningRun.is_current.is_(True),
                    ScreeningRun.status == "success",
                ),
            )
            .where(ScoringResult.company_id == company_id)
            .order_by(desc(ScoringResult.id))
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def add(
        self,
        company_id: uuid.UUID,
        scoring_result_id: uuid.UUID | None,
        created_by: uuid.UUID,
    ) -> LonglistItem:
        """ロングリスト項目を作成する."""
        item = LonglistItem(
            company_id=company_id,
            scoring_result_id=scoring_result_id,
            status="candidate",
            created_by=created_by,
            created_at=datetime.utcnow(),
        )
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def update(self, item: LonglistItem) -> LonglistItem:
        """変更済みの項目を永続化する."""
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def delete(self, item: LonglistItem) -> None:
        """項目を削除する."""
        await self.session.delete(item)
        await self.session.commit()
