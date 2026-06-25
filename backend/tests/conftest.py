import pytest
from httpx import AsyncClient

from app.core.database import AsyncSessionLocal
from app.core.security import create_access_token
from app.main import app
from app.repositories.user_repository import UserRepository


@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def analyst_user():
    """シードされた analyst ユーザーを取得"""
    async with AsyncSessionLocal() as session:
        repo = UserRepository(session)
        user = await repo.get_by_email("analyst@example.com")
        return user


@pytest.fixture
async def auth_cookies(analyst_user):
    """有効な access_token Cookie を生成"""
    token = create_access_token({"sub": str(analyst_user.id)})
    return {"access_token": token}
