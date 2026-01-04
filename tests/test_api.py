"""
FortifAI API Tests
"""
import pytest
from httpx import AsyncClient
from backend.api.main import app

@pytest.fixture
def anyio_backend():
    return 'asyncio'

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.mark.anyio
async def test_health_check(client):
    """Test health endpoint"""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

@pytest.mark.anyio
async def test_root_endpoint(client):
    """Test root endpoint"""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "FortifAI Security Platform"

@pytest.mark.anyio
async def test_readiness_check(client):
    """Test readiness endpoint"""
    response = await client.get("/ready")
    assert response.status_code == 200

@pytest.mark.anyio
async def test_liveness_check(client):
    """Test liveness endpoint"""
    response = await client.get("/live")
    assert response.status_code == 200
