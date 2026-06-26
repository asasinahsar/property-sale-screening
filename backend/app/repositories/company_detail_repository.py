"""CompanyDetailRepository - 企業詳細データ取得リポジトリ."""

import uuid
from dataclasses import dataclass, field

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.company import Company, FinancialData, QualitativeSignal
from app.models.screening import ScreeningRun, ScoringResult


@dataclass
class CompanyDetailData:
    """企業詳細データの構造体."""

    company: Company
    scoring: ScoringResult | None
    financial: FinancialData | None
    signals_support: list[QualitativeSignal] = field(default_factory=list)
    signals_counter: list[QualitativeSignal] = field(default_factory=list)


class CompanyDetailRepository:
    """企業詳細データを一括取得するリポジトリ."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_company_detail(
        self, company_id: uuid.UUID
    ) -> CompanyDetailData | None:
        """指定 company_id の企業詳細データを取得する。

        - Company が存在しない場合 None を返す
        - is_current=True & status='success' の ScreeningRun に紐づく ScoringResult を取得
        - 最新 as_of_date の FinancialData を取得
        - QualitativeSignal を Document ごと eager load
        """
        # 1. Company 取得
        company_stmt = select(Company).where(Company.id == company_id)
        company_result = await self.session.execute(company_stmt)
        companies = company_result.scalars().all()
        if not companies:
            return None
        company = companies[0]

        # 2. ScoringResult 取得 (is_current=True & status='success' の最新)
        scoring_stmt = (
            select(ScoringResult)
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
        scoring_result = await self.session.execute(scoring_stmt)
        scorings = scoring_result.scalars().all()
        scoring = scorings[0] if scorings else None

        # 3. FinancialData 取得 (最新 as_of_date)
        financial_stmt = (
            select(FinancialData)
            .where(FinancialData.company_id == company_id)
            .order_by(desc(FinancialData.as_of_date))
            .limit(1)
        )
        financial_result = await self.session.execute(financial_stmt)
        financials = financial_result.scalars().all()
        financial = financials[0] if financials else None

        # 4. QualitativeSignal 取得 (Document を eager load)
        signals_stmt = (
            select(QualitativeSignal)
            .where(QualitativeSignal.company_id == company_id)
            .options(selectinload(QualitativeSignal.document))
        )
        signals_result = await self.session.execute(signals_stmt)
        all_signals = list(signals_result.scalars().all())

        signals_support = [s for s in all_signals if s.stance == "support"]
        signals_counter = [s for s in all_signals if s.stance == "counter"]

        return CompanyDetailData(
            company=company,
            scoring=scoring,
            financial=financial,
            signals_support=signals_support,
            signals_counter=signals_counter,
        )
