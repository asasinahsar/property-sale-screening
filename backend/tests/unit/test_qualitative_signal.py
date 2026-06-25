"""QualitativeSignalService の Mock LLM ユニットテスト（RED フェーズ）."""

import uuid

import pytest
from fastapi import HTTPException

from app.api.v1.schemas.scoring import (
    ExtractedSignalSchema,
    SignalExtractionRequestSchema,
    SignalExtractionResponseSchema,
    SignalTypeEnum,
    StanceEnum,
)
from app.services.qualitative_signal import QualitativeSignalService


class MockLLMAgent:
    """正常にシグナルを返す Mock LLM Agent."""

    def __call__(
        self, request: SignalExtractionRequestSchema
    ) -> SignalExtractionResponseSchema:
        return SignalExtractionResponseSchema(
            signals=[
                ExtractedSignalSchema(
                    signal_type=SignalTypeEnum.ACTIVIST_PROPOSAL,
                    stance=StanceEnum.SUPPORT,
                    strength=0.85,
                    quote_text="当社は不動産売却を提案する",
                    source_page=12,
                )
            ],
            summary="アクティビストシグナル1件検出",
        )


class FailingMockLLMAgent:
    """LLM 呼び出しが失敗する Mock LLM Agent."""

    def __call__(self, request):
        raise RuntimeError("LLM API timeout")


class EmptyMockLLMAgent:
    """シグナルなしを返す Mock LLM Agent."""

    def __call__(self, request):
        return SignalExtractionResponseSchema(signals=[], summary="シグナルなし")


class NoQuoteMockLLMAgent:
    """引用文が空のシグナルを含む結果を返す Mock LLM Agent.

    Pydantic の min_length 制約を回避するため model_construct を用いて
    引用文が空のシグナルを直接生成する。
    """

    def __call__(self, request):
        invalid_signal = ExtractedSignalSchema.model_construct(
            signal_type=SignalTypeEnum.SALE_SUGGESTION,
            stance=StanceEnum.SUPPORT,
            strength=0.5,
            quote_text="",
            source_page=3,
        )
        valid_signal = ExtractedSignalSchema(
            signal_type=SignalTypeEnum.ACTIVIST_PROPOSAL,
            stance=StanceEnum.SUPPORT,
            strength=0.9,
            quote_text="不動産売却を強く要求する",
            source_page=5,
        )
        return SignalExtractionResponseSchema.model_construct(
            signals=[invalid_signal, valid_signal],
            summary="1件は引用なし",
        )


def _request() -> SignalExtractionRequestSchema:
    return SignalExtractionRequestSchema(
        document_id=uuid.uuid4(),
        document_text="本資料では不動産事業の売却について検討している。",
        company_name="テスト不動産",
    )


class TestQualitativeSignalService:
    """定性シグナル抽出サービスのテスト."""

    def test_extract_signals_returns_signals_from_mock_llm(self):
        """Mock LLM が正常なシグナルを返すこと."""
        service = QualitativeSignalService(llm_agent=MockLLMAgent())
        result = service.extract_signals(_request())

        assert isinstance(result, SignalExtractionResponseSchema)
        assert len(result.signals) == 1
        assert result.signals[0].signal_type == SignalTypeEnum.ACTIVIST_PROPOSAL
        assert result.signals[0].strength == 0.85

    def test_extract_signals_empty_result_returns_empty_list(self):
        """シグナルなしの場合は空リストを返すこと."""
        service = QualitativeSignalService(llm_agent=EmptyMockLLMAgent())
        result = service.extract_signals(_request())

        assert result.signals == []

    def test_extract_signals_llm_failure_raises_503(self):
        """LLM 呼び出し失敗で HTTPException(503) が発生すること."""
        service = QualitativeSignalService(llm_agent=FailingMockLLMAgent())

        with pytest.raises(HTTPException) as exc_info:
            service.extract_signals(_request())

        assert exc_info.value.status_code == 503

    def test_extract_signals_signal_without_quote_is_rejected(self):
        """引用文が空のシグナルは除外されること."""
        service = QualitativeSignalService(llm_agent=NoQuoteMockLLMAgent())
        result = service.extract_signals(_request())

        assert all(s.quote_text.strip() != "" for s in result.signals)
        assert len(result.signals) == 1

    def test_extract_signals_preserves_document_id(self):
        """document_id が正しく保持されること."""
        request = _request()
        service = QualitativeSignalService(llm_agent=MockLLMAgent())
        result = service.extract_signals(request)

        assert result.document_id == request.document_id
