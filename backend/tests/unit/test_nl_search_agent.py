"""AnthropicNLSearchAgent のユニットテスト（test モードのモック挙動）."""

import pytest

from app.api.v1.schemas.company_search import SearchConditionSchema
from app.llm.nl_search_agent import AnthropicNLSearchAgent


@pytest.fixture
def test_mode(monkeypatch):
    monkeypatch.setattr(
        "app.llm.nl_search_agent.settings.LLM_MODE", "test", raising=False
    )


def test_test_mode_extracts_unrealized_gain_and_industry(test_mode):
    agent = AnthropicNLSearchAgent()
    result = agent("含み益500億以上の小売業")
    assert isinstance(result, SearchConditionSchema)
    assert result.unrealized_gain_min == 500.0
    assert result.industry == "小売"


def test_test_mode_extracts_pbr(test_mode):
    agent = AnthropicNLSearchAgent()
    result = agent("PBR1倍割れの企業")
    assert result.pbr_max == 1.0


def test_test_mode_raises_on_unparseable(test_mode):
    agent = AnthropicNLSearchAgent()
    with pytest.raises(ValueError):
        agent("解釈できない無意味な文字列")


def test_test_mode_does_not_require_api_key(test_mode):
    # API キー無しでもインスタンス化できる（クライアントは遅延生成）
    agent = AnthropicNLSearchAgent()
    assert agent is not None
