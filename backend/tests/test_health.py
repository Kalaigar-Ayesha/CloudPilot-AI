import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_liveness_endpoint(client: AsyncClient):
    """Checks the liveness probe responds successfully."""
    response = await client.get("/api/v1/health/live")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["status"] == "UP"


@pytest.mark.asyncio
async def test_readiness_endpoint(client: AsyncClient):
    """Checks the readiness probe returns state results."""
    response = await client.get("/api/v1/health/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in ("success", "error")
    assert "db" in body["data"]
    assert "redis" in body["data"]


@pytest.mark.asyncio
async def test_health_combined_endpoint(client: AsyncClient):
    """Checks the overall health probe response structure."""
    response = await client.get("/api/v1/health/health")
    assert response.status_code == 200
    body = response.json()
    assert "application" in body["data"]
    assert "services" in body["data"]
