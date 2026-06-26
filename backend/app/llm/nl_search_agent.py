"""自然言語検索の条件抽出 LLM Agent（Anthropic Claude）.

日本語の検索クエリから SearchConditionSchema に対応するフィルタ条件を抽出する。
LLM_MODE=test の場合は外部 API を呼ばず、決定的なモックを返す。
"""

import json
import re

from app.api.v1.schemas.company_search import SearchConditionSchema
from app.core.config import settings

_SYSTEM_PROMPT = """\
あなたは不動産売却スクリーニングの検索アシスタントです。
ユーザーが日本語で入力した検索クエリから、企業を絞り込むためのフィルタ条件を抽出してください。

抽出可能な条件（該当しないものは null）:
- unrealized_gain_min: 含み益の下限（億円, 数値）
- unrealized_gain_max: 含み益の上限（億円, 数値）
- region: 地域（例: 関西, 関東）
- industry: 業種（例: 小売, 不動産, 製造）
- pbr_max: PBR の上限（例: 1.0 = PBR1倍割れ）
- pbr_min: PBR の下限
- structure_score_min: 構造スコアの下限（0-100）
- company_name: 企業名（完全一致したい場合のみ）
- securities_code: 証券コード（4桁数字など）

以下のJSON形式のみを返してください（説明文は不要）:
{
  "unrealized_gain_min": null,
  "unrealized_gain_max": null,
  "region": null,
  "industry": null,
  "pbr_max": null,
  "pbr_min": null,
  "structure_score_min": null,
  "company_name": null,
  "securities_code": null
}
条件が1つも読み取れない場合は、全フィールドが null のJSONを返してください。"""


class AnthropicNLSearchAgent:
    """自然言語クエリから検索条件を抽出するエージェント."""

    def __init__(self) -> None:
        self._client = None  # 遅延生成（test モードでは生成しない）
        self._model = settings.ANTHROPIC_MODEL

    def _get_client(self):
        if self._client is None:
            import anthropic

            self._client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        return self._client

    def __call__(self, query: str) -> SearchConditionSchema:
        if settings.LLM_MODE == "test":
            return self._mock_extract(query)
        return self._llm_extract(query)

    # ------------------------------------------------------------------
    # test モード: 決定的なモック
    # ------------------------------------------------------------------

    def _mock_extract(self, query: str) -> SearchConditionSchema:
        if "含み益500" in query and "小売" in query:
            return SearchConditionSchema(unrealized_gain_min=500.0, industry="小売")
        if "PBR" in query:
            return SearchConditionSchema(pbr_max=1.0)
        raise ValueError("解釈失敗")

    # ------------------------------------------------------------------
    # production モード: Anthropic Claude
    # ------------------------------------------------------------------

    def _llm_extract(self, query: str) -> SearchConditionSchema:
        message = self._get_client().messages.create(
            model=self._model,
            max_tokens=512,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": query}],
        )
        raw = message.content[0].text.strip()
        json_match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not json_match:
            raise ValueError("解釈失敗: JSON が抽出できませんでした")

        parsed = json.loads(json_match.group())
        return SearchConditionSchema(**parsed)
