"""企業ランキングエンドポイント."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user
from app.api.v1.schemas.scoring import (
    CompanyListResponse,
    CompanyRankingItemSchema,
    ConfidenceLevelEnum,
)
from app.core.dependencies import get_db
from app.models.company import Company, QualitativeSignal
from app.models.screening import ScreeningRun, ScoringResult
from app.models.user import User

router = APIRouter(prefix="/api/v1/companies", tags=["companies"])


@router.get("", response_model=CompanyListResponse)
async def get_companies(
    industry: str | None = Query(None, description="業種フィルタ"),
    min_score: float | None = Query(None, description="最低スコア"),
    max_score: float | None = Query(None, description="最高スコア"),
    has_event: bool | None = Query(None, description="イベントシグナルの有無"),
    sort_by: str = Query("total_score", description="ソートキー"),
    page: int = Query(1, ge=1, description="ページ番号（1始まり）"),
    page_size: int = Query(20, ge=1, le=200, description="1ページあたりの件数"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CompanyListResponse:
    """企業ランキング一覧を取得する（is_current=True のスクリーニング結果から）."""
    # is_current=True かつ success の run_id を取得
    run_stmt = (
        select(ScreeningRun.id)
        .where(
            and_(
                ScreeningRun.is_current == True,  # noqa: E712
                ScreeningRun.status == "success",
            )
        )
        .limit(1)
    )
    run_result = await db.execute(run_stmt)
    current_run_id = run_result.scalar_one_or_none()

    if current_run_id is None:
        # スクリーニング未実行: 空のレスポンスを返す
        return CompanyListResponse(items=[], total=0, page=page, page_size=page_size)

    # has_event 判定: QualitativeSignal が存在するか
    has_event_subq = (
        select(QualitativeSignal.id)
        .where(QualitativeSignal.company_id == Company.id)
        .correlate(Company)
        .exists()
    )

    # 基本クエリ: Company JOIN ScoringResult
    base_conditions = [ScoringResult.screening_run_id == current_run_id]

    if industry is not None:
        base_conditions.append(Company.industry == industry)
    if min_score is not None:
        base_conditions.append(ScoringResult.total_score >= min_score)
    if max_score is not None:
        base_conditions.append(ScoringResult.total_score <= max_score)
    if has_event is True:
        base_conditions.append(has_event_subq)
    elif has_event is False:
        base_conditions.append(~has_event_subq)

    # ソートカラム決定
    sort_col_map = {
        "total_score": ScoringResult.total_score,
        "structure_score": ScoringResult.structure_score,
        "event_score": ScoringResult.event_score,
    }
    sort_col = sort_col_map.get(sort_by, ScoringResult.total_score)

    # 総件数
    count_stmt = (
        select(func.count())
        .select_from(ScoringResult)
        .join(Company, ScoringResult.company_id == Company.id)
        .where(and_(*base_conditions))
    )
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    # データ取得
    offset = (page - 1) * page_size
    data_stmt = (
        select(
            Company,
            ScoringResult,
            has_event_subq.label("has_event"),
        )
        .join(ScoringResult, ScoringResult.company_id == Company.id)
        .where(and_(*base_conditions))
        .order_by(sort_col.desc())
        .offset(offset)
        .limit(page_size)
    )
    rows = await db.execute(data_stmt)
    results = rows.all()

    items = [
        CompanyRankingItemSchema(
            company_id=company.id,
            securities_code=company.securities_code,
            name=company.name,
            industry=company.industry,
            market_cap=float(company.market_cap)
            if company.market_cap is not None
            else None,
            total_score=float(scoring.total_score),
            structure_score=float(scoring.structure_score),
            event_score=float(scoring.event_score),
            event_boost=float(scoring.event_boost)
            if scoring.event_boost is not None
            else None,
            confidence=ConfidenceLevelEnum(scoring.confidence),
            unrealized_gain=None,  # FinancialData は JOIN していないため暫定 None
            has_event=bool(he),
        )
        for company, scoring, he in results
    ]

    return CompanyListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )
