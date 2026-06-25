import pytest


@pytest.mark.asyncio
async def test_me_returns_current_user(client, auth_cookies, analyst_user):
    """正常系: 有効な access_token で現在のユーザー情報を返す"""
    resp = await client.get("/api/v1/auth/me", cookies=auth_cookies)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == str(analyst_user.id)
    assert data["login_email"] == "analyst@example.com"
    assert data["role"] == "analyst"


@pytest.mark.asyncio
async def test_me_without_token_returns_401(client):
    """異常系: トークンなしは 401"""
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_with_invalid_token_returns_401(client):
    """異常系: 不正なトークンは 401"""
    resp = await client.get(
        "/api/v1/auth/me", cookies={"access_token": "invalid.token.value"}
    )
    assert resp.status_code == 401
