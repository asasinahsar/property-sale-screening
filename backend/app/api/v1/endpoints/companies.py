"""企業ランキングエンドポイント."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user
from app.api.v1.dependencies.search import get_company_search_service
from app.api.v1.schemas.company_search import CompanySearchResponse
from app.api.v1.schemas.company_detail import (
    CompanyDetailSchema,
    DocumentSummarySchema,
    FinancialDataDetailSchema,
    QualitativeSignalDetailSchema,
    ReportGenerateRequest,
    ReportGenerateResponse,
    ScoreBreakdownDetailSchema,
)
from app.api.v1.schemas.scoring import (
    CompanyListResponse,
    CompanyRankingItemSchema,
    ConfidenceLevelEnum,
)
from app.core.dependencies import get_db
from app.models.company import Company, QualitativeSignal
from app.models.screening import ScreeningRun, ScoringResult
from app.models.user import User
from app.repositories.company_detail_repository import CompanyDetailRepository
from app.services.company_search_service import CompanySearchService
from app.services.report_service import ReportService

router = APIRouter(prefix="/api/v1/companies", tags=["companies"])


@router.get("", response_model=CompanySearchResponse)
async def get_companies(
    q: str | None = Query(
        None, description="自然言語検索クエリ（最大200字）。LLM で条件抽出"
    ),
    company_name: str | None = Query(None, description="企業名（完全一致）"),
    securities_code: str | None = Query(None, description="証券コード（完全一致）"),
    industry: str | None = Query(None, description="業種フィルタ"),
    min_score: float | None = Query(None, description="最低スコア"),
    max_score: float | None = Query(None, description="最高スコア"),
    has_event: bool | None = Query(None, description="イベントシグナルの有無"),
    sort_by: str = Query("total_score", description="ソートキー"),
    page: int = Query(1, ge=1, description="ページ番号（1始まり）"),
    page_size: int = Query(20, ge=1, le=200, description="1ページあたりの件数"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    search_service: CompanySearchService = Depends(get_company_search_service),
) -> CompanySearchResponse:
    """企業ランキング一覧 / 検索を取得する（is_current=True のスクリーニング結果から）.

    - q / company_name / securities_code が指定された場合は検索サービスに委譲する。
    - いずれも無い場合は従来のランキング一覧を返す。
    """
    if q is not None or company_name is not None or securities_code is not None:
        return await search_service.search(
            q=q,
            company_name=company_name,
            securities_code=securities_code,
            industry=industry,
            sort_by=sort_by,
            page=page,
            page_size=page_size,
        )

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


@router.get("/{company_id}", response_model=CompanyDetailSchema, status_code=200)
async def get_company_detail(
    company_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CompanyDetailSchema:
    """企業詳細を取得する."""
    detail = await CompanyDetailRepository(db).get_company_detail(company_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Company not found")

    signals_support = [
        QualitativeSignalDetailSchema(
            signal_id=s.id,
            signal_type=s.signal_type,
            stance=s.stance,
            strength=float(s.strength) if s.strength is not None else None,
            quote_text=s.quote_text,
            source_page=s.source_page,
            document=DocumentSummarySchema(
                document_id=s.document.id,
                document_type=s.document.document_type,
                disclosed_at=s.document.disclosed_at,
                source_url=s.document.source_url,
            ),
        )
        for s in detail.signals_support
    ]

    signals_counter = [
        QualitativeSignalDetailSchema(
            signal_id=s.id,
            signal_type=s.signal_type,
            stance=s.stance,
            strength=float(s.strength) if s.strength is not None else None,
            quote_text=s.quote_text,
            source_page=s.source_page,
            document=DocumentSummarySchema(
                document_id=s.document.id,
                document_type=s.document.document_type,
                disclosed_at=s.document.disclosed_at,
                source_url=s.document.source_url,
            ),
        )
        for s in detail.signals_counter
    ]

    return CompanyDetailSchema(
        company_id=detail.company.id,
        securities_code=detail.company.securities_code,
        name=detail.company.name,
        industry=detail.company.industry,
        market_cap=float(detail.company.market_cap)
        if detail.company.market_cap is not None
        else None,
        scoring=ScoreBreakdownDetailSchema.model_validate(detail.scoring)
        if detail.scoring
        else None,
        financial=FinancialDataDetailSchema.model_construct(
            **{
                k: (float(v) if v is not None else None)
                for k, v in {
                    "as_of_date": detail.financial.as_of_date,
                    "revenue": detail.financial.revenue,
                    "pbr": detail.financial.pbr,
                    "adjusted_pbr": detail.financial.adjusted_pbr,
                    "equity_ratio": detail.financial.equity_ratio,
                    "re_market_value": detail.financial.re_market_value,
                    "re_book_value": detail.financial.re_book_value,
                    "unrealized_gain": detail.financial.unrealized_gain,
                    "unrealized_gain_ratio": detail.financial.unrealized_gain_ratio,
                    "roic": detail.financial.roic,
                    "wacc": detail.financial.wacc,
                    "stock_price": detail.financial.stock_price,
                }.items()
                if k not in ("as_of_date",)
            },
            as_of_date=detail.financial.as_of_date,
        )
        if detail.financial
        else None,
        signals_support=signals_support,
        signals_counter=signals_counter,
    )


@router.post(
    "/{company_id}/report", response_model=ReportGenerateResponse, status_code=202
)
async def generate_report(
    company_id: uuid.UUID,
    request: ReportGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReportGenerateResponse:
    """PDF レポートを非同期生成する（202 Accepted）."""
    detail = await CompanyDetailRepository(db).get_company_detail(company_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Company not found")

    return await ReportService(db).generate_report(
        company_id, current_user.id, request.format
    )
