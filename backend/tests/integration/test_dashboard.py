import pytest


@pytest.mark.asyncio
async def test_dashboard_kpi_returns_values(client, auth_cookies):
    """正常系: 認証済みで KPI を返す（スケルトン仮値）"""
    resp = await client.get("/api/v1/dashboard/kpi", cookies=auth_cookies)
    assert resp.status_code == 200
    data = resp.json()
    assert "total_companies" in data
    assert "high_score_companies" in data
    assert "avg_score" in data
    assert "event_count" in data
    assert isinstance(data["total_companies"], int)
    assert isinstance(data["avg_score"], float)


@pytest.mark.asyncio
async def test_dashboard_kpi_without_token_returns_401(client):
    """異常系: トークンなしは 401"""
    resp = await client.get("/api/v1/dashboard/kpi")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_health_returns_healthy(client):
    """正常系: ALB 用ヘルスチェック（認証不要）"""
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "healthy"}
