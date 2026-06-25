"""Anthropic Claude を使った定性シグナル抽出 LLM Agent."""

import json
import re

import anthropic

from app.api.v1.schemas.scoring import (
    ExtractedSignalSchema,
    SignalExtractionRequestSchema,
    SignalExtractionResponseSchema,
    SignalTypeEnum,
    StanceEnum,
)
from app.core.config import settings

_SYSTEM_PROMPT = """\
あなたは不動産売却スクリーニングの専門アナリストです。
与えられた開示文書から、以下3種類の定性シグナルを抽出してください。

シグナル種別:
- activist_proposal: アクティビスト株主による不動産売却・資本効率改善の提案
- capital_efficiency_target: 経営陣による資本効率目標の明示（ROE/ROIC目標など）
- sale_suggestion: 不動産売却・売却検討の示唆

各シグナルについて以下を必ず含めること:
- signal_type: 上記3種別のいずれか
- stance: "support"（売却方向）または "counter"（売却否定・現状維持）
- strength: 0.0〜1.0（シグナルの強さ）
- quote_text: 文書中の引用文（必須。存在しない場合はシグナルを除外）
- source_page: ページ番号（不明な場合は1）

出典のないシグナルは除外してください。

以下のJSON形式で回答してください:
{
  "signals": [
    {
      "signal_type": "activist_proposal",
      "stance": "support",
      "strength": 0.8,
      "quote_text": "引用文",
      "source_page": 5
    }
  ],
  "summary": "抽出結果の要約"
}
シグナルがなければ signals は空配列にしてください。必ずJSONのみを返してください。"""


class AnthropicLLMAgent:
    """Anthropic Claude API を使った定性シグナル抽出エージェント."""

    def __init__(self) -> None:
        self._client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self._model = settings.ANTHROPIC_MODEL

    def __call__(
        self, request: SignalExtractionRequestSchema
    ) -> SignalExtractionResponseSchema:
        user_message = (
            f"企業名: {request.company_name}\n\n"
            f"文書ID: {request.document_id}\n\n"
            f"--- 文書本文 ---\n{request.document_text[:8000]}"  # トークン節約のため先頭8000文字
        )

        message = self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )

        raw = message.content[0].text.strip()
        # JSON部分だけ抽出（コードブロックが付く場合を考慮）
        json_match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not json_match:
            return SignalExtractionResponseSchema(
                document_id=request.document_id,
                signals=[],
                summary="シグナルの抽出結果なし",
            )

        parsed = json.loads(json_match.group())
        signals = []
        for s in parsed.get("signals", []):
            try:
                signals.append(
                    ExtractedSignalSchema(
                        signal_type=SignalTypeEnum(s["signal_type"]),
                        stance=StanceEnum(s["stance"]),
                        strength=float(s["strength"]),
                        quote_text=str(s["quote_text"]),
                        source_page=int(s.get("source_page", 1)),
                    )
                )
            except (KeyError, ValueError):
                continue

        return SignalExtractionResponseSchema(
            document_id=request.document_id,
            signals=signals,
            summary=parsed.get("summary", ""),
        )
