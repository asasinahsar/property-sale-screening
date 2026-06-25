"""IntegrationScoringService のユニットテスト（RED フェーズ）."""

import uuid

from app.api.v1.schemas.scoring import (
    ConfidenceLevelEnum,
    IntegratedScoringInputSchema,
    IntegratedScoringOutputSchema,
)
from app.services.integration_scoring import IntegrationScoringService


def _input(
    structure_score: float,
    event_score: float,
    event_boost: float,
) -> IntegratedScoringInputSchema:
    return IntegratedScoringInputSchema(
        company_id=uuid.uuid4(),
        structure_score=structure_score,
        event_score=event_score,
        event_boost=event_boost,
    )


class TestIntegrationScoringService:
    """統合スコア算出サービスのテスト."""

    def test_integrate_returns_valid_total_score(self):
        """正常入力で total_score が算出されること."""
        service = IntegrationScoringService()
        result = service.integrate(_input(70.0, 50.0, 1.2))

        assert isinstance(result, IntegratedScoringOutputSchema)
        assert result.total_score >= 0.0

    def test_integrate_total_score_increases_with_boost(self):
        """event_boost が高いほど total_score が高いこと."""
        service = IntegrationScoringService()

        low_boost = service.integrate(_input(60.0, 60.0, 1.0))
        high_boost = service.integrate(_input(60.0, 60.0, 2.0))

        assert high_boost.total_score > low_boost.total_score

    def test_integrate_confidence_high_when_both_scores_high(self):
        """structure/event 両方高いと confidence=HIGH であること."""
        service = IntegrationScoringService()
        result = service.integrate(_input(90.0, 90.0, 1.5))

        assert result.confidence == ConfidenceLevelEnum.HIGH

    def test_integrate_confidence_low_when_both_scores_low(self):
        """両方低いと confidence=LOW であること."""
        service = IntegrationScoringService()
        result = service.integrate(_input(10.0, 10.0, 1.0))

        assert result.confidence == ConfidenceLevelEnum.LOW

    def test_integrate_total_score_formula(self):
        """total_score の算出が0以上であること（計算式は実装に合わせる想定）."""
        service = IntegrationScoringService()
        result = service.integrate(_input(80.0, 40.0, 1.3))

        assert result.total_score >= 0.0

    def test_integrate_score_breakdown_has_required_keys(self):
        """score_breakdown に "structure", "event", "boost" キーが含まれること."""
        service = IntegrationScoringService()
        result = service.integrate(_input(70.0, 50.0, 1.2))

        assert "structure" in result.score_breakdown
        assert "event" in result.score_breakdown
        assert "boost" in result.score_breakdown
