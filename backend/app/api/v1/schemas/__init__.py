"""Schemas module - API層DTO.

barrel export最小化のため、個別スキーマはここにexportしない。

【直接importパターン】
    # 推奨: 直接import
    from app.api.v1.schemas.auth import LoginRequest, MeResponse, DashboardKpiResponse
    from app.api.v1.schemas.user import UserCreate, UserResponse
    from app.api.v1.schemas.scoring import (
        FinancialDataInputSchema,
        StructureScoreOutputSchema,
        SignalExtractionRequestSchema,
        SignalExtractionResponseSchema,
        EventScoringInputSchema,
        EventScoreOutputSchema,
        IntegratedScoringInputSchema,
        IntegratedScoringOutputSchema,
        ScreeningRunResponse,
        ScreeningTriggerResponse,
        CompanyRankingItemSchema,
        CompanyListResponse,
    )

    # 非推奨: barrel import
    # from app.api.v1.schemas import UserCreate
"""
