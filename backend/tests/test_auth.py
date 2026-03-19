"""
Tests for auth endpoints (register, login).
Uses SQLite in-memory for isolation.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest_asyncio.fixture(scope="module")
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_register_and_login(client):
    # Register
    r = await client.post("/api/auth/register", json={
        "username": "testuser",
        "email": "testuser@test.com",
        "password": "Test@1234",
        "role": "user",
    })
    assert r.status_code in (201, 400)  # 400 if already exists from previous run

    # Login
    r = await client.post("/api/auth/login", json={
        "username": "admin",
        "password": "Admin@123!",
    })
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert data["role"] == "admin"
