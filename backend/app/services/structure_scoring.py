"""構造スコア算出サービス."""

import math

from app.api.v1.schemas.scoring import (
    FinancialDataInputSchema,
    StructureScoreBreakdownSchema,
    StructureScoreOutputSchema,
)

# 加重平均の重み
_PBR_WEIGHT = 0.30
_EQUITY_RATIO_WEIGHT = 0.20
_UNREALIZED_GAIN_WEIGHT = 0.35
_ROIC_WACC_WEIGHT = 0.15

# None の場合に使う中央値スコア
_NEUTRAL_SCORE = 0.5


def _sigmoid(x: float) -> float:
    """シグモイド関数（0–1 の範囲に変換）."""
    return 1.0 / (1.0 + math.exp(-x))


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _std(values: list[float], mean: float) -> float:
    if len(values) < 2:
        return 1.0
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    return math.sqrt(variance) if variance > 0 else 1.0


def _zscore_to_unit(z: float) -> float:
    """z-score を sigmoid で [0,1] に変換."""
    return _sigmoid(z)


class StructureScoringService:
    """構造スコア算出サービス."""

    def calculate(
        self,
        input: FinancialDataInputSchema,
        peers: list[FinancialDataInputSchema] | None = None,
    ) -> StructureScoreOutputSchema:
        """財務データから構造スコアを算出する."""
        if peers is not None and len(peers) >= 2:
            score = self._calculate_with_peers(input, peers)
        else:
            score = self._calculate_standalone(input)

        breakdown = StructureScoreBreakdownSchema(
            pbr_contribution=_PBR_WEIGHT,
            equity_ratio_contribution=_EQUITY_RATIO_WEIGHT,
            unrealized_gain_contribution=_UNREALIZED_GAIN_WEIGHT,
            roic_wacc_contribution=_ROIC_WACC_WEIGHT,
        )

        return StructureScoreOutputSchema(
            company_id=input.company_id,
            structure_score=round(max(0.0, min(100.0, score * 100.0)), 6),
            breakdown=breakdown,
        )

    # ------------------------------------------------------------------
    # スタンドアローン（業種比較なし）
    # ------------------------------------------------------------------

    def _calculate_standalone(self, input: FinancialDataInputSchema) -> float:
        """業種比較なしで各指標を [0,1] に変換して加重平均."""
        pbr_score = self._pbr_to_score(input.pbr, input.adjusted_pbr)
        equity_score = self._equity_ratio_to_score(input.equity_ratio)
        unrealized_score = self._unrealized_gain_ratio_to_score(
            input.unrealized_gain_ratio
        )
        roic_wacc_score = self._roic_wacc_to_score(input.roic, input.wacc)

        return (
            pbr_score * _PBR_WEIGHT
            + equity_score * _EQUITY_RATIO_WEIGHT
            + unrealized_score * _UNREALIZED_GAIN_WEIGHT
            + roic_wacc_score * _ROIC_WACC_WEIGHT
        )

    def _pbr_to_score(self, pbr: float | None, adjusted_pbr: float | None) -> float:
        """PBR を [0,1] スコアに変換（低いほど高スコア）."""
        value = pbr if pbr is not None else adjusted_pbr
        if value is None:
            return _NEUTRAL_SCORE
        return max(0.0, 1.0 - value / 5.0)

    def _equity_ratio_to_score(self, equity_ratio: float | None) -> float:
        """自己資本比率を [0,1] スコアに変換（高いほど高スコア）."""
        if equity_ratio is None:
            return _NEUTRAL_SCORE
        return max(0.0, min(1.0, equity_ratio))

    def _unrealized_gain_ratio_to_score(self, ratio: float | None) -> float:
        """含み益倍率を [0,1] スコアに変換（高いほど高スコア）."""
        if ratio is None:
            return _NEUTRAL_SCORE
        # 0–2 の範囲でクリッピング
        return max(0.0, min(1.0, ratio / 2.0))

    def _roic_wacc_to_score(self, roic: float | None, wacc: float | None) -> float:
        """ROIC - WACC ギャップを [0,1] スコアに変換."""
        if roic is None or wacc is None:
            return _NEUTRAL_SCORE
        gap = roic - wacc
        # [-0.1, 0.1] の範囲を [0, 1] にマップ
        return max(0.0, min(1.0, (gap + 0.1) / 0.2))

    # ------------------------------------------------------------------
    # 業種内正規化（z-score）
    # ------------------------------------------------------------------

    def _calculate_with_peers(
        self,
        input: FinancialDataInputSchema,
        peers: list[FinancialDataInputSchema],
    ) -> float:
        """業種内 z-score 正規化を使って加重平均スコアを算出."""
        pbr_score = self._zscore_metric(
            self._get_pbr(input),
            [self._get_pbr(p) for p in peers],
            higher_is_better=False,
        )
        equity_score = self._zscore_metric(
            input.equity_ratio,
            [p.equity_ratio for p in peers],
            higher_is_better=True,
        )
        unrealized_score = self._zscore_metric(
            input.unrealized_gain_ratio,
            [p.unrealized_gain_ratio for p in peers],
            higher_is_better=True,
        )
        roic_wacc_score = self._zscore_metric(
            self._get_roic_wacc_gap(input),
            [self._get_roic_wacc_gap(p) for p in peers],
            higher_is_better=True,
        )

        return (
            pbr_score * _PBR_WEIGHT
            + equity_score * _EQUITY_RATIO_WEIGHT
            + unrealized_score * _UNREALIZED_GAIN_WEIGHT
            + roic_wacc_score * _ROIC_WACC_WEIGHT
        )

    def _get_pbr(self, input: FinancialDataInputSchema) -> float | None:
        if input.pbr is not None:
            return input.pbr
        return input.adjusted_pbr

    def _get_roic_wacc_gap(self, input: FinancialDataInputSchema) -> float | None:
        if input.roic is not None and input.wacc is not None:
            return input.roic - input.wacc
        return None

    def _zscore_metric(
        self,
        value: float | None,
        peer_values: list[float | None],
        higher_is_better: bool,
    ) -> float:
        """指標の業種内 z-score を [0,1] に変換して返す."""
        valid_values = [v for v in peer_values if v is not None]
        if not valid_values or value is None:
            return _NEUTRAL_SCORE

        mean = _mean(valid_values)
        std = _std(valid_values, mean)

        z = (value - mean) / std
        if not higher_is_better:
            z = -z

        return _sigmoid(z)
