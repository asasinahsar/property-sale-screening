"""LonglistRepository のユニットテスト（RED フェーズ）.

実 DB には接続せず AsyncMock で差し替えたセッションを使う。
LonglistRepository は longlist_items の CRUD と、一覧取得時に
Company / ScoringResult / FinancialData を JOIN した行を返す想定。
"""

import uuid
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock

from app.repositories.longlist_repository import LonglistRepository


# ---------------------------------------------------------------------------
# ダミーモデル生成ヘルパー
# ---------------------------------------------------------------------------


def _make_company(company_id: uuid.UUID) -> MagicMock:
    c = MagicMock()
    c.id = company_id
    c.securities_code = "1234"
    c.name = "テスト不動産"
    c.industry = "不動産"
    c.market_cap = 1000.0
    return c


def _make_scoring(company_id: uuid.UUID) -> MagicMock:
    sr = MagicMock()
    sr.id = uuid.uuid4()
    sr.company_id = company_id
    sr.structure_score = 80.0
    sr.event_score = 60.0
    sr.total_score = 88.0
    return sr


def _make_financial(company_id: uuid.UUID) -> MagicMock:
    fd = MagicMock()
    fd.company_id = company_id
    fd.as_of_date = date(2025, 3, 31)
    fd.unrealized_gain = 400.0
    return fd


def _make_item(company_id: uuid.UUID, status: str = "candidate") -> MagicMock:
    item = MagicMock()
    item.id = uuid.uuid4()
    item.company_id = company_id
    item.scoring_result_id = uuid.uuid4()
    item.status = status
    item.reason_memo = None
    item.created_by = uuid.uuid4()
    item.created_at = datetime(2025, 6, 25, 9, 0, 0)
    item.approved_by = None
    item.approved_at = None
    return item


def _make_session_with_rows(rows: list) -> AsyncMock:
    """list_items 用: execute().all() が rows を返すセッション。"""
    session = AsyncMock()
    result = MagicMock()
    result.all.return_value = rows
    session.execute.return_value = result
    return session


class TestLonglistRepositoryList:
    """list_items の取得ロジック."""

    async def test_list_items_returns_rows(self):
        """Company/Scoring/Financial を JOIN した行を返すこと."""
        company_id = uuid.uuid4()
        item = _make_item(company_id)
        company = _make_company(company_id)
        scoring = _make_scoring(company_id)
        financial = _make_financial(company_id)

        session = _make_session_with_rows([(item, company, scoring, financial)])
        repo = LonglistRepository(session)

        result = await repo.list_items()

        assert len(result) == 1
        row = result[0]
        assert row.item.id == item.id
        assert row.company.id == company_id
        assert row.scoring is not None
        assert row.financial is not None

    async def test_list_items_empty(self):
        """項目がない場合は空リストを返すこと."""
        session = _make_session_with_rows([])
        repo = LonglistRepository(session)

        result = await repo.list_items()

        assert result == []


class TestLonglistRepositoryGet:
    """get_by_id / get_by_company_id."""

    async def test_get_by_id_found(self):
        company_id = uuid.uuid4()
        item = _make_item(company_id)
        session = AsyncMock()
        session.get.return_value = item
        repo = LonglistRepository(session)

        result = await repo.get_by_id(item.id)

        assert result is item

    async def test_get_by_id_not_found(self):
        session = AsyncMock()
        session.get.return_value = None
        repo = LonglistRepository(session)

        result = await repo.get_by_id(uuid.uuid4())

        assert result is None

    async def test_get_by_company_id_found(self):
        company_id = uuid.uuid4()
        item = _make_item(company_id)
        session = AsyncMock()
        exec_result = MagicMock()
        exec_result.scalar_one_or_none.return_value = item
        session.execute.return_value = exec_result
        repo = LonglistRepository(session)

        result = await repo.get_by_company_id(company_id)

        assert result is item

    async def test_get_by_company_id_not_found(self):
        session = AsyncMock()
        exec_result = MagicMock()
        exec_result.scalar_one_or_none.return_value = None
        session.execute.return_value = exec_result
        repo = LonglistRepository(session)

        result = await repo.get_by_company_id(uuid.uuid4())

        assert result is None


class TestLonglistRepositoryMutations:
    """add / update / delete."""

    async def test_add_persists_item(self):
        company_id = uuid.uuid4()
        user_id = uuid.uuid4()
        scoring_id = uuid.uuid4()
        session = AsyncMock()
        repo = LonglistRepository(session)

        item = await repo.add(
            company_id=company_id,
            scoring_result_id=scoring_id,
            created_by=user_id,
        )

        session.add.assert_called_once()
        session.commit.assert_awaited()
        assert item.company_id == company_id
        assert item.created_by == user_id
        assert item.scoring_result_id == scoring_id
        assert item.status == "candidate"

    async def test_update_commits(self):
        company_id = uuid.uuid4()
        item = _make_item(company_id)
        session = AsyncMock()
        repo = LonglistRepository(session)

        await repo.update(item)

        session.commit.assert_awaited()

    async def test_delete_removes_item(self):
        company_id = uuid.uuid4()
        item = _make_item(company_id)
        session = AsyncMock()
        repo = LonglistRepository(session)

        await repo.delete(item)

        session.delete.assert_awaited_once_with(item)
        session.commit.assert_awaited()

    async def test_count_returns_total(self):
        session = AsyncMock()
        exec_result = MagicMock()
        exec_result.scalar_one.return_value = 3
        session.execute.return_value = exec_result
        repo = LonglistRepository(session)

        total = await repo.count()

        assert total == 3
