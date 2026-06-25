"""イベントスコア算出サービス."""

from app.api.v1.schemas.scoring import (
    EventScoreOutputSchema,
    EventScoringInputSchema,
    SignalTypeEnum,
    StanceEnum,
)

_SIGNAL_WEIGHTS: dict[SignalTypeEnum, float] = {
    SignalTypeEnum.ACTIVIST_PROPOSAL: 3.0,
    SignalTypeEnum.CAPITAL_EFFICIENCY_TARGET: 2.0,
    SignalTypeEnum.SALE_SUGGESTION: 2.5,
    SignalTypeEnum.OTHER: 1.0,
}


class EventScoringService:
    """イベントスコア算出サービス."""

    def calculate(self, input: EventScoringInputSchema) -> EventScoreOutputSchema:
        """定性シグナル一覧からイベントスコアとブースト係数を算出する."""
        if not input.signals:
            return EventScoreOutputSchema(
                company_id=input.company_id,
                event_score=0.0,
                event_boost=1.0,
            )

        raw_score = 0.0
        for signal in input.signals:
            weight = _SIGNAL_WEIGHTS.get(signal.signal_type, 1.0)
            base_contribution = weight * signal.strength

            if signal.stance == StanceEnum.COUNTER:
                base_contribution *= -1

            if signal.recency_days is not None:
                recency_factor = max(0.0, 1.0 - signal.recency_days / 365.0)
                base_contribution *= 1.0 + recency_factor * 0.5

            raw_score += base_contribution

        event_score = max(0.0, min(100.0, raw_score * 10))
        event_boost = max(1.0, min(2.0, 1.0 + raw_score / 20))

        return EventScoreOutputSchema(
            company_id=input.company_id,
            event_score=event_score,
            event_boost=event_boost,
        )
