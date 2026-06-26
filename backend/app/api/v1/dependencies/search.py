"""自然言語検索 Agent / 企業検索サービスの依存注入."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.llm.nl_search_agent import AnthropicNLSearchAgent
from app.services.company_search_service import CompanySearchService


def get_nl_search_agent() -> AnthropicNLSearchAgent:
    """自然言語検索 Agent を返す."""
    return AnthropicNLSearchAgent()


def get_company_search_service(
    db: AsyncSession = Depends(get_db),
    nl_agent: AnthropicNLSearchAgent = Depends(get_nl_search_agent),
) -> CompanySearchService:
    """企業検索サービスを返す."""
    return CompanySearchService(session=db, nl_agent=nl_agent)
