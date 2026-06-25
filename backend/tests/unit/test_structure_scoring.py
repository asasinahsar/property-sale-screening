"""StructureScoringService のユニットテスト（RED フェーズ）."""

import uuid

import pytest

from app.api.v1.schemas.scoring import (
    FinancialDataInputSchema,
    StructureScoreOutputSchema,
)
from app.services.structure_scoring import StructureScoringService


def _high_score_input() -> FinancialDataInputSchema:
    """割安・高効率（高スコア想定）の財務データ."""
    return FinancialDataInputSchema(
        company_id=uuid.uuid4(),
        pbr=0.5,  # 低PBR（割安）
        adjusted_pbr=0.6,
        equity_ratio=0.7,  # 高自己資本比率
        unrealized_gain=500.0,
        unrealized_gain_ratio=0.8,
        roic=0.12,
        wacc=0.05,  # ROIC > WACC（良好）
        industry="不動産",
    )


def _low_score_input() -> FinancialDataInputSchema:
    """割高・低効率（低スコア想定）の財務データ."""
    return FinancialDataInputSchema(
        company_id=uuid.uuid4(),
        pbr=3.0,  # 高PBR（割高）
        adjusted_pbr=3.5,
        equity_ratio=0.2,
        unrealized_gain=10.0,
        unrealized_gain_ratio=0.05,
        roic=0.02,
        wacc=0.08,  # ROIC < WACC（非効率）
        industry="不動産",
    )


class TestStructureScoringService:
    """構造スコア算出サービスのテスト."""

    def test_calculate_returns_score_between_0_and_100(self):
        """正常な財務データで0-100のスコアが返ること."""
        service = StructureScoringService()
        result = service.calculate(_high_score_input())

        assert isinstance(result, StructureScoreOutputSchema)
        assert 0.0 <= result.structure_score <= 100.0

    def test_calculate_with_all_none_returns_low_score(self):
        """全指標がNoneでも動作し、最低スコアを返すこと."""
        service = StructureScoringService()
        all_none_input = FinancialDataInputSchema(
            company_id=uuid.uuid4(),
            pbr=None,
            adjusted_pbr=None,
            equity_ratio=None,
            unrealized_gain=None,
            unrealized_gain_ratio=None,
            roic=None,
            wacc=None,
            industry="不動産",
        )

        result = service.calculate(all_none_input)

        assert 0.0 <= result.structure_score <= 100.0

    def test_calculate_breakdown_sums_to_one(self):
        """breakdownの4寄与度の合計が1.0（浮動小数点許容誤差あり）であること."""
        service = StructureScoringService()
        result = service.calculate(_high_score_input())

        total = (
            result.breakdown.pbr_contribution
            + result.breakdown.equity_ratio_contribution
            + result.breakdown.unrealized_gain_contribution
            + result.breakdown.roic_wacc_contribution
        )

        assert total == pytest.approx(1.0, abs=1e-6)

    def test_calculate_higher_pbr_leads_to_lower_score(self):
        """PBRが高い（割高）ほど構造スコアが低いこと."""
        service = StructureScoringService()

        high_result = service.calculate(_high_score_input())
        low_result = service.calculate(_low_score_input())

        assert high_result.structure_score > low_result.structure_score

    def test_calculate_negative_roic_wacc_gap_penalizes_score(self):
        """ROIC < WACC のとき ROIC/WACC 寄与が低下すること."""
        service = StructureScoringService()

        good = FinancialDataInputSchema(
            company_id=uuid.uuid4(),
            pbr=1.0,
            adjusted_pbr=1.0,
            equity_ratio=0.5,
            unrealized_gain=100.0,
            unrealized_gain_ratio=0.3,
            roic=0.15,
            wacc=0.05,  # ROIC > WACC
            industry="不動産",
        )
        bad = FinancialDataInputSchema(
            company_id=uuid.uuid4(),
            pbr=1.0,
            adjusted_pbr=1.0,
            equity_ratio=0.5,
            unrealized_gain=100.0,
            unrealized_gain_ratio=0.3,
            roic=0.02,
            wacc=0.08,  # ROIC < WACC
            industry="不動産",
        )

        good_result = service.calculate(good)
        bad_result = service.calculate(bad)

        assert good_result.structure_score > bad_result.structure_score

    def test_calculate_industry_normalization_same_industry(self):
        """同一業種の2社を比較すると相対化されること."""
        service = StructureScoringService()

        company_a = _high_score_input()
        company_b = _low_score_input()

        result_a = service.calculate(company_a, peers=[company_a, company_b])
        result_b = service.calculate(company_b, peers=[company_a, company_b])

        # 同一業種内で相対化され、割安な企業のスコアが高くなる
        assert result_a.structure_score > result_b.structure_score
