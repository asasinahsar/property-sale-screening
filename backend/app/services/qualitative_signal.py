"""定性シグナル抽出サービス."""

from fastapi import HTTPException

from app.api.v1.schemas.scoring import (
    SignalExtractionRequestSchema,
    SignalExtractionResponseSchema,
)


class QualitativeSignalService:
    """定性シグナル抽出サービス（LLM Agent ラッパー）."""

    def __init__(self, llm_agent) -> None:
        self.llm_agent = llm_agent

    def extract_signals(
        self, request: SignalExtractionRequestSchema
    ) -> SignalExtractionResponseSchema:
        """LLM Agent を呼び出してシグナルを抽出し、無効シグナルを除外する."""
        try:
            response = self.llm_agent(request)
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail={"code": "LLM_CALL_FAILED", "message": str(e)},
            ) from e

        # 引用文が空白のみのシグナルを除外
        valid_signals = [s for s in response.signals if s.quote_text.strip() != ""]

        return SignalExtractionResponseSchema(
            document_id=request.document_id,
            signals=valid_signals,
            summary=response.summary,
        )
