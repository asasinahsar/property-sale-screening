"""ロングリスト管理・承認フロー＆エクスポートエンドポイント."""

import uuid

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user
from app.api.v1.schemas.longlist import (
    LonglistApprovalRequest,
    LonglistCreateRequest,
    LonglistExportResponse,
    LonglistItemSchema,
    LonglistListResponse,
    LonglistUpdateRequest,
)
from app.core.dependencies import get_db
from app.models.user import User
from app.services.longlist_service import LonglistService

router = APIRouter(prefix="/api/v1/longlist", tags=["longlist"])


@router.get("", response_model=LonglistListResponse, status_code=200)
async def get_longlist(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LonglistListResponse:
    """ロングリスト一覧を取得する."""
    return await LonglistService(db).list_longlist()


@router.post("", response_model=LonglistItemSchema, status_code=201)
async def add_longlist(
    request: LonglistCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LonglistItemSchema:
    """企業をロングリストに追加する（重複時 409）."""
    return await LonglistService(db).add_to_longlist(
        request.company_id, current_user.id
    )


@router.patch("/{item_id}", response_model=LonglistItemSchema, status_code=200)
async def update_longlist(
    item_id: uuid.UUID,
    request: LonglistUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LonglistItemSchema:
    """ロングリストのメモ・ステータスを更新する."""
    return await LonglistService(db).update_longlist(
        item_id, request.reason_memo, request.status
    )


@router.post("/{item_id}/approval", response_model=LonglistItemSchema, status_code=200)
async def approve_longlist(
    item_id: uuid.UUID,
    request: LonglistApprovalRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LonglistItemSchema:
    """ロングリスト項目を承認/却下する（manager ロールのみ）."""
    return await LonglistService(db).set_approval(item_id, request.action, current_user)


@router.delete("/{item_id}", status_code=204)
async def delete_longlist(
    item_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """ロングリストから企業を削除する."""
    await LonglistService(db).delete_from_longlist(item_id)
    return Response(status_code=204)


@router.post("/export", response_model=LonglistExportResponse, status_code=202)
async def export_longlist(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LonglistExportResponse:
    """ロングリストを CSV にエクスポートする（202 Accepted、0 件時 409）."""
    return await LonglistService(db).export_longlist(current_user.id)
