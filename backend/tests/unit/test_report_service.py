"""ReportService のユニットテスト（RED フェーズ）.

ReportService は根拠レポート（PDF）生成リクエストを受け付け、
GeneratedFile レコードを作成する。生成は非同期処理（pending → ...）を
想定しており、ここでは DB アクセスをモックしてレコード作成と
ステータス管理のロジックのみを検証する。
"""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

# RED: まだ実装が存在しないため ImportError になる想定
from app.services.report_service import ReportService  # noqa: E402


def _make_session() -> AsyncMock:
    """add/commit/refresh を持つモックセッション."""
    session = AsyncMock()
    session.add = MagicMock()

    async def _refresh(obj):
        # commit 後に id / created_at が確定する挙動を模倣
        if getattr(obj, "id", None) is None:
            obj.id = uuid.uuid4()
        if getattr(obj, "created_at", None) is None:
            obj.created_at = datetime(2025, 6, 25, 12, 0, 0)
        return None

    session.refresh.side_effect = _refresh
    return session


class TestReportServiceGenerate:
    """generate_report のテスト."""

    async def test_generate_report_creates_generated_file_record(self):
        """GeneratedFile が DB に追加されること（session.add が呼ばれる）."""
        session = _make_session()
        service = ReportService(session)

        await service.generate_report(
            company_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            format="pdf",
        )

        assert session.add.called
        session.commit.assert_awaited()

    async def test_generate_report_returns_file_id(self):
        """戻り値に file_id（UUID）が含まれること."""
        session = _make_session()
        service = ReportService(session)

        result = await service.generate_report(
            company_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            format="pdf",
        )

        assert isinstance(result.file_id, uuid.UUID)

    async def test_generate_report_sets_status_pending(self):
        """初期ステータスが 'pending' であること."""
        session = _make_session()
        service = ReportService(session)

        result = await service.generate_report(
            company_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            format="pdf",
        )

        assert result.status == "pending"


class TestReportServiceGetStatus:
    """get_file_status のテスト."""

    async def test_get_file_status_returns_file_info(self):
        """GeneratedFile を取得してステータス情報を返すこと."""
        file_id = uuid.uuid4()

        gen_file = MagicMock()
        gen_file.id = file_id
        gen_file.format = "pdf"
        gen_file.status = "completed"
        gen_file.s3_key = "reports/xxxx.pdf"
        gen_file.created_at = datetime(2025, 6, 25, 12, 0, 0)

        session = _make_session()
        session.get = AsyncMock(return_value=gen_file)

        service = ReportService(session)
        result = await service.get_file_status(file_id)

        assert result.file_id == file_id
        assert result.format == "pdf"
        assert result.status == "completed"

    async def test_get_file_status_not_found_raises_404(self):
        """存在しない file_id では 404 HTTPException を送出すること."""
        session = _make_session()
        session.get = AsyncMock(return_value=None)

        service = ReportService(session)

        with pytest.raises(HTTPException) as exc_info:
            await service.get_file_status(uuid.uuid4())

        assert exc_info.value.status_code == 404
