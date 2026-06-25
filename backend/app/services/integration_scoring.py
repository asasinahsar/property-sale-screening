"""統合スコア算出サービス."""

from app.api.v1.schemas.scoring import (
    ConfidenceLevelEnum,
    IntegratedScoringInputSchema,
    IntegratedScoringOutputSchema,
)


class IntegrationScoringService:
    """統合スコアを算出するサービス."""

    def integrate(
        self,
        input: IntegratedScoringInputSchema,
    ) -> IntegratedScoringOutputSchema:
        """構造スコア・イベントスコア・ブースト係数から統合スコアを算出する."""
        structure_score = input.structure_score
        event_score = input.event_score
        event_boost = input.event_boost

        # 統合スコア算出
        total_score = structure_score * 0.6 + event_score * 0.4 * event_boost
        total_score = max(0.0, min(200.0, total_score))

        # 信頼度判定
        avg_score = (structure_score + event_score) / 2
        if avg_score >= 60:
            confidence = ConfidenceLevelEnum.HIGH
        elif avg_score >= 30:
            confidence = ConfidenceLevelEnum.MID
        else:
            confidence = ConfidenceLevelEnum.LOW

        # スコア内訳
        score_breakdown = {
            "structure": round(structure_score, 2),
            "event": round(event_score, 2),
            "boost": round(event_boost, 2),
            "total": round(total_score, 2),
        }

        return IntegratedScoringOutputSchema(
            company_id=input.company_id,
            total_score=total_score,
            confidence=confidence,
            ai_judgment=None,
            judgment_refs=None,
            score_breakdown=score_breakdown,
        )
