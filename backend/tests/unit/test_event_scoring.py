"""EventScoringService のユニットテスト（RED フェーズ）."""

import uuid

from app.api.v1.schemas.scoring import (
    EventScoreOutputSchema,
    EventScoringInputSchema,
    QualitativeSignalInputSchema,
    SignalTypeEnum,
    StanceEnum,
)
from app.services.event_scoring import EventScoringService


def _input(signals: list[QualitativeSignalInputSchema]) -> EventScoringInputSchema:
    return EventScoringInputSchema(company_id=uuid.uuid4(), signals=signals)


class TestEventScoringService:
    """イベントスコア算出サービスのテスト."""

    def test_calculate_no_signals_returns_base_score(self):
        """シグナルなしは event_score=0, event_boost=1.0 であること."""
        service = EventScoringService()
        result = service.calculate(_input([]))

        assert isinstance(result, EventScoreOutputSchema)
        assert result.event_score == 0.0
        assert result.event_boost == 1.0

    def test_calculate_activist_proposal_highest_weight(self):
        """activist_proposal は最も高いスコアを生むこと."""
        service = EventScoringService()

        activist = service.calculate(
            _input(
                [
                    QualitativeSignalInputSchema(
                        signal_type=SignalTypeEnum.ACTIVIST_PROPOSAL,
                        stance=StanceEnum.SUPPORT,
                        strength=0.8,
                        recency_days=30,
                    )
                ]
            )
        )
        other = service.calculate(
            _input(
                [
                    QualitativeSignalInputSchema(
                        signal_type=SignalTypeEnum.OTHER,
                        stance=StanceEnum.SUPPORT,
                        strength=0.8,
                        recency_days=30,
                    )
                ]
            )
        )

        assert activist.event_score > other.event_score

    def test_counter_signal_reduces_score(self):
        """stance=counter のシグナルはスコアを下げること."""
        service = EventScoringService()

        support = service.calculate(
            _input(
                [
                    QualitativeSignalInputSchema(
                        signal_type=SignalTypeEnum.SALE_SUGGESTION,
                        stance=StanceEnum.SUPPORT,
                        strength=0.7,
                        recency_days=30,
                    )
                ]
            )
        )
        counter = service.calculate(
            _input(
                [
                    QualitativeSignalInputSchema(
                        signal_type=SignalTypeEnum.SALE_SUGGESTION,
                        stance=StanceEnum.COUNTER,
                        strength=0.7,
                        recency_days=30,
                    )
                ]
            )
        )

        assert counter.event_score < support.event_score

    def test_recency_recent_signal_boosts_score(self):
        """最近のシグナル（recency_days=10）は古いもの（365日）より加点が大きいこと."""
        service = EventScoringService()

        recent = service.calculate(
            _input(
                [
                    QualitativeSignalInputSchema(
                        signal_type=SignalTypeEnum.ACTIVIST_PROPOSAL,
                        stance=StanceEnum.SUPPORT,
                        strength=0.7,
                        recency_days=10,
                    )
                ]
            )
        )
        old = service.calculate(
            _input(
                [
                    QualitativeSignalInputSchema(
                        signal_type=SignalTypeEnum.ACTIVIST_PROPOSAL,
                        stance=StanceEnum.SUPPORT,
                        strength=0.7,
                        recency_days=365,
                    )
                ]
            )
        )

        assert recent.event_score > old.event_score

    def test_event_boost_max_is_2_0(self):
        """event_boost は 2.0 を超えないこと."""
        service = EventScoringService()

        many_strong_signals = [
            QualitativeSignalInputSchema(
                signal_type=SignalTypeEnum.ACTIVIST_PROPOSAL,
                stance=StanceEnum.SUPPORT,
                strength=1.0,
                recency_days=1,
            )
            for _ in range(50)
        ]
        result = service.calculate(_input(many_strong_signals))

        assert result.event_boost <= 2.0

    def test_event_score_max_is_100(self):
        """event_score は 100 を超えないこと."""
        service = EventScoringService()

        many_strong_signals = [
            QualitativeSignalInputSchema(
                signal_type=SignalTypeEnum.ACTIVIST_PROPOSAL,
                stance=StanceEnum.SUPPORT,
                strength=1.0,
                recency_days=1,
            )
            for _ in range(50)
        ]
        result = service.calculate(_input(many_strong_signals))

        assert result.event_score <= 100.0

    def test_multiple_signals_accumulate_correctly(self):
        """複数シグナルの加算が正しく行われること."""
        service = EventScoringService()

        single = service.calculate(
            _input(
                [
                    QualitativeSignalInputSchema(
                        signal_type=SignalTypeEnum.SALE_SUGGESTION,
                        stance=StanceEnum.SUPPORT,
                        strength=0.5,
                        recency_days=30,
                    )
                ]
            )
        )
        multiple = service.calculate(
            _input(
                [
                    QualitativeSignalInputSchema(
                        signal_type=SignalTypeEnum.SALE_SUGGESTION,
                        stance=StanceEnum.SUPPORT,
                        strength=0.5,
                        recency_days=30,
                    ),
                    QualitativeSignalInputSchema(
                        signal_type=SignalTypeEnum.CAPITAL_EFFICIENCY_TARGET,
                        stance=StanceEnum.SUPPORT,
                        strength=0.5,
                        recency_days=30,
                    ),
                ]
            )
        )

        assert multiple.event_score > single.event_score
