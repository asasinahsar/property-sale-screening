"""CompanyDetailRepository のユニットテスト（RED フェーズ）.

実際の DB には接続せず、AsyncMock で差し替えたセッションを使う。
get_company_detail は Company + FinancialData + ScoringResult +
QualitativeSignal（document eager load）を取得し、stance ごとに
support / counter のシグナルを分離した構造体を返す想定。
"""

import uuid
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock


# RED: まだ実装が存在しないため ImportError になる想定
from app.repositories.company_detail_repository import (  # noqa: E402
    CompanyDetailRepository,
)


# ---------------------------------------------------------------------------
# テスト用のダミーモデルインスタンス生成ヘルパー
# ---------------------------------------------------------------------------


def _make_company(company_id: uuid.UUID | None = None) -> MagicMock:
    company = MagicMock()
    company.id = company_id or uuid.uuid4()
    company.securities_code = "1234"
    company.name = "テスト不動産"
    company.industry = "不動産"
    company.market_cap = 1000.0
    return company


def _make_financial(company_id: uuid.UUID) -> MagicMock:
    fd = MagicMock()
    fd.company_id = company_id
    fd.as_of_date = date(2025, 3, 31)
    fd.revenue = 500.0
    fd.pbr = 0.6
    fd.adjusted_pbr = 0.7
    fd.equity_ratio = 0.65
    fd.re_market_value = 800.0
    fd.re_book_value = 400.0
    fd.unrealized_gain = 400.0
    fd.unrealized_gain_ratio = 0.4
    fd.roic = 0.12
    fd.wacc = 0.05
    fd.stock_price = 1500.0
    return fd


def _make_scoring(company_id: uuid.UUID) -> MagicMock:
    sr = MagicMock()
    sr.id = uuid.uuid4()
    sr.company_id = company_id
    sr.structure_score = 80.0
    sr.event_score = 60.0
    sr.total_score = 88.0
    sr.event_boost = 1.1
    sr.confidence = "high"
    sr.ai_judgment = "割安かつ含み益が大きい"
    sr.judgment_refs = {"signal_ids": []}
    sr.score_breakdown = {"structure": 80.0, "event": 60.0}
    return sr


def _make_signal(company_id: uuid.UUID, stance: str) -> MagicMock:
    doc = MagicMock()
    doc.id = uuid.uuid4()
    doc.document_type = "yuho"
    doc.disclosed_at = date(2025, 1, 15)
    doc.source_url = "https://example.com/doc.pdf"

    sig = MagicMock()
    sig.id = uuid.uuid4()
    sig.company_id = company_id
    sig.document_id = doc.id
    sig.signal_type = "activist_proposal"
    sig.stance = stance
    sig.strength = 0.8
    sig.recency = date(2025, 1, 15)
    sig.source_page = 12
    sig.quote_text = "保有不動産の売却を提案する"
    sig.created_at = datetime(2025, 1, 16, 9, 0, 0)
    sig.document = doc
    return sig


def _make_session(scalar_results: list) -> AsyncMock:
    """session.execute が呼ばれるたびに scalar_results を順に返すモック。

    各要素は execute の戻り値 result に対する scalars().all() /
    scalar_one_or_none() の戻り値として解釈する。
    """
    session = AsyncMock()

    call_index = {"i": 0}

    async def _execute(*_args, **_kwargs):
        idx = call_index["i"]
        call_index["i"] += 1
        payload = scalar_results[idx] if idx < len(scalar_results) else None

        result = MagicMock()
        scalars = MagicMock()
        scalars.all.return_value = payload if isinstance(payload, list) else []
        result.scalars.return_value = scalars
        if isinstance(payload, list):
            result.scalar_one_or_none.return_value = payload[0] if payload else None
        else:
            result.scalar_one_or_none.return_value = payload
        return result

    session.execute.side_effect = _execute
    return session


class TestCompanyDetailRepository:
    """get_company_detail の取得ロジックのテスト."""

    # ------------------------------------------------------------------
    # 正常系
    # ------------------------------------------------------------------

    async def test_get_company_detail_returns_company_with_all_relations(self):
        """Company + Financial + Scoring + Signal を含む詳細を返すこと."""
        company_id = uuid.uuid4()
        company = _make_company(company_id)
        financial = _make_financial(company_id)
        scoring = _make_scoring(company_id)
        support = _make_signal(company_id, "support")
        counter = _make_signal(company_id, "counter")

        # execute の呼び出し順は実装依存のため、すべての関連を一括で返せるよう
        # 代表的なパターン（company, scoring, financial, signals）を並べる
        session = _make_session(
            [
                [company],
                [scoring],
                [financial],
                [support, counter],
            ]
        )
        repo = CompanyDetailRepository(session)

        detail = await repo.get_company_detail(company_id)

        assert detail is not None
        assert detail.company.id == company_id
        assert detail.scoring is not None
        assert detail.financial is not None
        assert len(detail.signals_support) + len(detail.signals_counter) == 2

    async def test_get_company_detail_signals_separated_by_stance(self):
        """support と counter が正しく分離されること."""
        company_id = uuid.uuid4()
        company = _make_company(company_id)
        scoring = _make_scoring(company_id)
        financial = _make_financial(company_id)
        support = _make_signal(company_id, "support")
        counter = _make_signal(company_id, "counter")

        session = _make_session(
            [
                [company],
                [scoring],
                [financial],
                [support, counter],
            ]
        )
        repo = CompanyDetailRepository(session)

        detail = await repo.get_company_detail(company_id)

        assert detail is not None
        assert all(s.stance == "support" for s in detail.signals_support)
        assert all(s.stance == "counter" for s in detail.signals_counter)
        assert len(detail.signals_support) == 1
        assert len(detail.signals_counter) == 1

    async def test_get_company_detail_no_scoring_returns_none_scoring(self):
        """is_current スクリーニングがない場合 scoring=None になること."""
        company_id = uuid.uuid4()
        company = _make_company(company_id)
        financial = _make_financial(company_id)

        session = _make_session(
            [
                [company],
                [],  # scoring なし
                [financial],
                [],  # signals なし
            ]
        )
        repo = CompanyDetailRepository(session)

        detail = await repo.get_company_detail(company_id)

        assert detail is not None
        assert detail.scoring is None

    async def test_get_company_detail_no_financial_returns_none_financial(self):
        """FinancialData がない場合 financial=None になること."""
        company_id = uuid.uuid4()
        company = _make_company(company_id)
        scoring = _make_scoring(company_id)

        session = _make_session(
            [
                [company],
                [scoring],
                [],  # financial なし
                [],  # signals なし
            ]
        )
        repo = CompanyDetailRepository(session)

        detail = await repo.get_company_detail(company_id)

        assert detail is not None
        assert detail.financial is None

    # ------------------------------------------------------------------
    # 異常系
    # ------------------------------------------------------------------

    async def test_get_company_detail_not_found_returns_none(self):
        """存在しない company_id では None を返すこと."""
        company_id = uuid.uuid4()
        session = _make_session(
            [
                [],  # company なし
            ]
        )
        repo = CompanyDetailRepository(session)

        detail = await repo.get_company_detail(company_id)

        assert detail is None
