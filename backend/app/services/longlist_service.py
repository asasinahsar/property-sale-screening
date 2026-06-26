"""LonglistService - ロングリスト管理・承認フロー＆エクスポートのビジネスロジック."""

import uuid
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.longlist import (
    LonglistExportResponse,
    LonglistItemSchema,
    LonglistListResponse,
)
from app.models.longlist import GeneratedFile, LonglistItem
from app.models.user import User
from app.repositories.longlist_repository import LonglistRepository, LonglistRow

MAX_MEMO_LENGTH = 500


class LonglistService:
    """ロングリスト管理サービス."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = LonglistRepository(session)

    # ------------------------------------------------------------------
    # 一覧
    # ------------------------------------------------------------------

    async def list_longlist(self) -> LonglistListResponse:
        """ロングリスト一覧を取得する."""
        rows = await self.repo.list_items()
        total = await self.repo.count()
        items = [self._row_to_schema(row) for row in rows]
        return LonglistListResponse(items=items, total=total)

    # ------------------------------------------------------------------
    # 追加
    # ------------------------------------------------------------------

    async def add_to_longlist(
        self, company_id: uuid.UUID, user_id: uuid.UUID
    ) -> LonglistItemSchema:
        """企業をロングリストに追加する（重複時 409）."""
        existing = await self.repo.get_by_company_id(company_id)
        if existing is not None:
            raise HTTPException(
                status_code=409,
                detail="ALREADY_EXISTS: company is already in the longlist",
            )

        scoring_result_id = await self.repo.find_current_scoring_result_id(company_id)
        item = await self.repo.add(
            company_id=company_id,
            scoring_result_id=scoring_result_id,
            created_by=user_id,
        )
        row = await self.repo.get_row_by_id(item.id)
        return self._row_to_schema(row)

    # ------------------------------------------------------------------
    # 更新（メモ・ステータス）
    # ------------------------------------------------------------------

    async def update_longlist(
        self,
        item_id: uuid.UUID,
        reason_memo: str | None,
        status: str | None,
    ) -> LonglistItemSchema:
        """メモ・ステータスを更新する."""
        if reason_memo is not None and len(reason_memo) > MAX_MEMO_LENGTH:
            raise HTTPException(
                status_code=422,
                detail=f"reason_memo must be at most {MAX_MEMO_LENGTH} characters",
            )

        item = await self._get_or_404(item_id)

        if reason_memo is not None:
            item.reason_memo = reason_memo
        if status is not None:
            item.status = status

        await self.repo.update(item)
        return await self._item_to_schema(item)

    # ------------------------------------------------------------------
    # 承認 / 却下（manager のみ）
    # ------------------------------------------------------------------

    async def set_approval(
        self, item_id: uuid.UUID, action: str, user: User
    ) -> LonglistItemSchema:
        """承認/却下する（manager ロールのみ）."""
        if user.role != "manager":
            raise HTTPException(
                status_code=403,
                detail="FORBIDDEN: only managers can approve or reject",
            )

        item = await self._get_or_404(item_id)
        item.status = "approved" if action == "approve" else "rejected"
        item.approved_by = user.id
        item.approved_at = datetime.utcnow()

        await self.repo.update(item)
        return await self._item_to_schema(item)

    # ------------------------------------------------------------------
    # 削除
    # ------------------------------------------------------------------

    async def delete_from_longlist(self, item_id: uuid.UUID) -> None:
        """ロングリストから削除する."""
        item = await self._get_or_404(item_id)
        await self.repo.delete(item)

    # ------------------------------------------------------------------
    # エクスポート（CSV）
    # ------------------------------------------------------------------

    async def export_longlist(self, user_id: uuid.UUID) -> LonglistExportResponse:
        """ロングリストを CSV にエクスポートする（非同期: 202 + file_id）.

        0 件の場合は 409 EMPTY_TARGET を返す。
        実際の CSV 生成は非同期バックグラウンドで行う想定（MVP では pending のまま）。
        """
        total = await self.repo.count()
        if total == 0:
            raise HTTPException(
                status_code=409,
                detail="EMPTY_TARGET: longlist has no items to export",
            )

        generated_file = GeneratedFile(
            id=uuid.uuid4(),
            created_by=user_id,
            company_id=None,
            file_kind="export",
            format="csv",
            status="pending",
            s3_key="",
            created_at=datetime.utcnow(),
        )
        self.session.add(generated_file)
        await self.session.commit()
        await self.session.refresh(generated_file)

        return LonglistExportResponse(
            file_id=generated_file.id,
            status=generated_file.status,
            download_url=None,
            created_at=generated_file.created_at,
        )

    # ------------------------------------------------------------------
    # ヘルパー
    # ------------------------------------------------------------------

    async def _get_or_404(self, item_id: uuid.UUID) -> LonglistItem:
        item = await self.repo.get_by_id(item_id)
        if item is None:
            raise HTTPException(status_code=404, detail="Longlist item not found")
        return item

    @staticmethod
    def _row_to_schema(row: LonglistRow) -> LonglistItemSchema:
        item = row.item
        scoring = row.scoring
        financial = row.financial
        return LonglistItemSchema(
            id=item.id,
            company_id=item.company_id,
            securities_code=row.company.securities_code,
            name=row.company.name,
            industry=row.company.industry,
            total_score=float(scoring.total_score)
            if scoring and scoring.total_score is not None
            else None,
            structure_score=float(scoring.structure_score)
            if scoring and scoring.structure_score is not None
            else None,
            event_score=float(scoring.event_score)
            if scoring and scoring.event_score is not None
            else None,
            unrealized_gain=float(financial.unrealized_gain)
            if financial and financial.unrealized_gain is not None
            else None,
            status=item.status,
            reason_memo=item.reason_memo,
            created_by=item.created_by,
            created_at=item.created_at,
            approved_by=item.approved_by,
            approved_at=item.approved_at,
        )

    async def _item_to_schema(self, item: LonglistItem) -> LonglistItemSchema:
        """単一 item からスコア・財務・企業情報を補完したスキーマを生成する."""
        row = await self.repo.get_row_by_id(item.id)
        if row is None:
            raise HTTPException(status_code=404, detail="Longlist item not found")
        return self._row_to_schema(row)
