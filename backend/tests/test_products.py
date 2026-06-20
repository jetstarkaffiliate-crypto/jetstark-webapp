import pytest
from httpx import AsyncClient
from tests.fixtures.data import TEST_USER, TEST_VENDOR, TEST_PRODUCT


@pytest.mark.asyncio
async def test_create_product(client: AsyncClient):
    await client.post("/api/auth/signup", json=TEST_VENDOR)
    login = await client.post("/api/auth/login", json={
        "email": TEST_VENDOR["email"],
        "password": TEST_VENDOR["password"],
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.post("/api/products", json=TEST_PRODUCT, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == TEST_PRODUCT["title"]
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_list_products(client: AsyncClient):
    resp = await client.get("/api/products")
    assert resp.status_code == 200
    data = resp.json()
    assert "products" in data


@pytest.mark.asyncio
async def test_create_product_unauthenticated(client: AsyncClient):
    resp = await client.post("/api/products", json=TEST_PRODUCT)
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_buyer_cannot_create_product(client: AsyncClient):
    await client.post("/api/auth/signup", json=TEST_USER)
    login = await client.post("/api/auth/login", json={
        "email": TEST_USER["email"],
        "password": TEST_USER["password"],
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.post("/api/products", json=TEST_PRODUCT, headers=headers)
    assert resp.status_code == 403
