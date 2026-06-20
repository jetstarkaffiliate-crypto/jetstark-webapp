import pytest
from httpx import AsyncClient
from tests.fixtures.data import TEST_USER


@pytest.mark.asyncio
async def test_signup(client: AsyncClient):
    resp = await client.post("/api/auth/signup", json=TEST_USER)
    assert resp.status_code == 201
    data = resp.json()
    assert data["user"]["email"] == TEST_USER["email"]
    assert data["user"]["role"] == "buyer"
    assert "id" in data["user"]
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_duplicate_signup(client: AsyncClient):
    await client.post("/api/auth/signup", json=TEST_USER)
    resp = await client.post("/api/auth/signup", json=TEST_USER)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    await client.post("/api/auth/signup", json=TEST_USER)
    resp = await client.post("/api/auth/login", json={
        "email": TEST_USER["email"],
        "password": TEST_USER["password"],
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    await client.post("/api/auth/signup", json=TEST_USER)
    resp = await client.post("/api/auth/login", json={
        "email": TEST_USER["email"],
        "password": "wrongpassword",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me(client: AsyncClient):
    await client.post("/api/auth/signup", json=TEST_USER)
    login_resp = await client.post("/api/auth/login", json={
        "email": TEST_USER["email"],
        "password": TEST_USER["password"],
    })
    token = login_resp.json()["access_token"]
    resp = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == TEST_USER["email"]
