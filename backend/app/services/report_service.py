"""根拠レポート生成サービス."""

import uuid
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.company_detail import FileStatusResponse, ReportGenerateResponse
from app.models.longlist import GeneratedFile


class ReportService:
    """根拠レポート生成サービス."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def generate_report(
        self,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        format: str = "pdf",
    ) -> ReportGenerateResponse:
        """
        GeneratedFile レコードを pending 状態で作成して file_id を返す。

        実際の PDF 生成は非同期バックグラウンドで行う想定（MVP では pending のまま）。
        """
        generated_file = GeneratedFile(
            company_id=company_id,
            created_by=user_id,
            file_kind="report",
            format=format,
            status="pending",
            s3_key="",
            created_at=datetime.utcnow(),
        )

        self.session.add(generated_file)
        await self.session.commit()
        await self.session.refresh(generated_file)

        return ReportGenerateResponse(
            file_id=generated_file.id,
            status=generated_file.status,
            download_url=None,
            created_at=generated_file.created_at,
        )

    async def get_file_status(self, file_id: uuid.UUID) -> FileStatusResponse:
        """
        GeneratedFile を取得してステータスを返す。

        存在しない場合は HTTPException(404) を raise する。
        """
        generated_file = await self.session.get(GeneratedFile, file_id)

        if generated_file is None:
            raise HTTPException(status_code=404, detail="File not found")

        download_url: str | None = None
        if generated_file.status == "completed":
            download_url = f"/api/v1/files/{file_id}/download"

        return FileStatusResponse(
            file_id=generated_file.id,
            status=generated_file.status,
            download_url=download_url,
            format=generated_file.format,
            created_at=generated_file.created_at,
        )
