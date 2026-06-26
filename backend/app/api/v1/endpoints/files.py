"""ファイル生成ステータスエンドポイント."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user
from app.api.v1.schemas.company_detail import FileStatusResponse
from app.core.dependencies import get_db
from app.models.user import User
from app.services.report_service import ReportService

router = APIRouter(prefix="/api/v1/files", tags=["files"])


@router.get("/{file_id}", response_model=FileStatusResponse, status_code=200)
async def get_file_status(
    file_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FileStatusResponse:
    """ファイル生成ステータスを取得する."""
    return await ReportService(db).get_file_status(file_id)
