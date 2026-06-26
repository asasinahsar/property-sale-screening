"""LonglistService のユニットテスト（RED フェーズ）.

Repository / session をモックし、ビジネスルールを検証する。
- 重複追加は 409
- メモ 500字超は 422
- approve/reject は manager のみ（それ以外 403）
- エクスポートは 0 件で 409 EMPTY_TARGET
"""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.repositories.longlist_repository import LonglistRow
from app.services.longlist_service import LonglistService


# ---------------------------------------------------------------------------
# ヘルパー
# ---------------------------------------------------------------------------


def _make_user(role: str) -> MagicMock:
    u = MagicMock()
    u.id = uuid.uuid4()
    u.role = role
    return u


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


def _make_row(company_id: uuid.UUID, item: MagicMock | None = None) -> LonglistRow:
    item = item or _make_item(company_id)
    company = MagicMock()
    company.id = company_id
    company.securities_code = "1234"
    company.name = "テスト不動産"
    company.industry = "不動産"
    scoring = MagicMock()
    scoring.total_score = 88.0
    scoring.structure_score = 80.0
    scoring.event_score = 60.0
    financial = MagicMock()
    financial.unrealized_gain = 400.0
    return LonglistRow(item=item, company=company, scoring=scoring, financial=financial)


def _service_with_repo(repo: AsyncMock) -> LonglistService:
    session = AsyncMock()
    svc = LonglistService(session)
    svc.repo = repo
    return svc


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------


class TestListLonglist:
    async def test_list_returns_items(self):
        company_id = uuid.uuid4()
        repo = AsyncMock()
        repo.list_items.return_value = [_make_row(company_id)]
        repo.count.return_value = 1
        svc = _service_with_repo(repo)

        result = await svc.list_longlist()

        assert result.total == 1
        assert len(result.items) == 1
        assert result.items[0].company_id == company_id
        assert result.items[0].total_score == 88.0
        assert result.items[0].unrealized_gain == 400.0


# ---------------------------------------------------------------------------
# add
# ---------------------------------------------------------------------------


class TestAddToLonglist:
    async def test_add_success(self):
        company_id = uuid.uuid4()
        user = _make_user("analyst")
        item = _make_item(company_id)
        repo = AsyncMock()
        repo.get_by_company_id.return_value = None  # 重複なし
        repo.find_current_scoring_result_id.return_value = uuid.uuid4()
        repo.add.return_value = item
        repo.get_row_by_id.return_value = _make_row(company_id, item)
        svc = _service_with_repo(repo)

        result = await svc.add_to_longlist(company_id, user.id)

        assert result.company_id == company_id
        repo.add.assert_awaited_once()

    async def test_add_duplicate_raises_409(self):
        company_id = uuid.uuid4()
        user = _make_user("analyst")
        repo = AsyncMock()
        repo.get_by_company_id.return_value = _make_item(company_id)  # 既存
        svc = _service_with_repo(repo)

        with pytest.raises(HTTPException) as exc:
            await svc.add_to_longlist(company_id, user.id)
        assert exc.value.status_code == 409


# ---------------------------------------------------------------------------
# update memo
# ---------------------------------------------------------------------------


class TestUpdateLonglist:
    async def test_update_memo_success(self):
        company_id = uuid.uuid4()
        item = _make_item(company_id)
        repo = AsyncMock()
        repo.get_by_id.return_value = item
        repo.get_row_by_id.return_value = _make_row(company_id, item)
        svc = _service_with_repo(repo)

        result = await svc.update_longlist(item.id, reason_memo="良い候補", status=None)

        assert result.reason_memo == "良い候補"
        repo.update.assert_awaited_once()

    async def test_update_memo_too_long_raises_422(self):
        company_id = uuid.uuid4()
        item = _make_item(company_id)
        repo = AsyncMock()
        repo.get_by_id.return_value = item
        svc = _service_with_repo(repo)

        with pytest.raises(HTTPException) as exc:
            await svc.update_longlist(item.id, reason_memo="あ" * 501, status=None)
        assert exc.value.status_code == 422

    async def test_update_not_found_raises_404(self):
        repo = AsyncMock()
        repo.get_by_id.return_value = None
        svc = _service_with_repo(repo)

        with pytest.raises(HTTPException) as exc:
            await svc.update_longlist(uuid.uuid4(), reason_memo="x", status=None)
        assert exc.value.status_code == 404


# ---------------------------------------------------------------------------
# approval
# ---------------------------------------------------------------------------


class TestApproval:
    async def test_approve_by_manager_success(self):
        company_id = uuid.uuid4()
        item = _make_item(company_id)
        manager = _make_user("manager")
        repo = AsyncMock()
        repo.get_by_id.return_value = item
        repo.get_row_by_id.return_value = _make_row(company_id, item)
        svc = _service_with_repo(repo)

        result = await svc.set_approval(item.id, "approve", manager)

        assert result.status == "approved"
        assert result.approved_by == manager.id
        assert result.approved_at is not None
        repo.update.assert_awaited_once()

    async def test_reject_by_manager_success(self):
        company_id = uuid.uuid4()
        item = _make_item(company_id)
        manager = _make_user("manager")
        repo = AsyncMock()
        repo.get_by_id.return_value = item
        repo.get_row_by_id.return_value = _make_row(company_id, item)
        svc = _service_with_repo(repo)

        result = await svc.set_approval(item.id, "reject", manager)

        assert result.status == "rejected"
        assert result.approved_by == manager.id

    async def test_approve_by_analyst_raises_403(self):
        company_id = uuid.uuid4()
        item = _make_item(company_id)
        analyst = _make_user("analyst")
        repo = AsyncMock()
        repo.get_by_id.return_value = item
        svc = _service_with_repo(repo)

        with pytest.raises(HTTPException) as exc:
            await svc.set_approval(item.id, "approve", analyst)
        assert exc.value.status_code == 403

    async def test_approval_not_found_raises_404(self):
        manager = _make_user("manager")
        repo = AsyncMock()
        repo.get_by_id.return_value = None
        svc = _service_with_repo(repo)

        with pytest.raises(HTTPException) as exc:
            await svc.set_approval(uuid.uuid4(), "approve", manager)
        assert exc.value.status_code == 404


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------


class TestDelete:
    async def test_delete_success(self):
        company_id = uuid.uuid4()
        item = _make_item(company_id)
        repo = AsyncMock()
        repo.get_by_id.return_value = item
        svc = _service_with_repo(repo)

        await svc.delete_from_longlist(item.id)

        repo.delete.assert_awaited_once_with(item)

    async def test_delete_not_found_raises_404(self):
        repo = AsyncMock()
        repo.get_by_id.return_value = None
        svc = _service_with_repo(repo)

        with pytest.raises(HTTPException) as exc:
            await svc.delete_from_longlist(uuid.uuid4())
        assert exc.value.status_code == 404


# ---------------------------------------------------------------------------
# export
# ---------------------------------------------------------------------------


class TestExport:
    async def test_export_success(self):
        user = _make_user("analyst")
        repo = AsyncMock()
        repo.count.return_value = 2
        svc = _service_with_repo(repo)

        result = await svc.export_longlist(user.id)

        assert result.file_id is not None
        assert result.status == "pending"

    async def test_export_empty_raises_409_empty_target(self):
        user = _make_user("analyst")
        repo = AsyncMock()
        repo.count.return_value = 0
        svc = _service_with_repo(repo)

        with pytest.raises(HTTPException) as exc:
            await svc.export_longlist(user.id)
        assert exc.value.status_code == 409
        assert "EMPTY_TARGET" in str(exc.value.detail)
