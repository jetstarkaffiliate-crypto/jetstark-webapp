import pytest
from httpx import AsyncClient
from tests.fixtures.data import TEST_USER, TEST_VENDOR, TEST_PRODUCT
from app.models.product import ProductStatus


@pytest.mark.asyncio
async def test_cart_empty_for_new_user(client: AsyncClient):
    buyer_data = {**TEST_USER, "email": "cart-empty@test.com"}
    await client.post("/api/auth/signup", json=buyer_data)
    login = await client.post("/api/auth/login", json={
        "email": buyer_data["email"],
        "password": buyer_data["password"],
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.get("/api/cart", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert len(data["items"]) == 0


@pytest.mark.asyncio
async def test_add_to_cart_unauthenticated(client: AsyncClient):
    resp = await client.post("/api/cart/items", json={
        "product_id": "fake-id",
        "quantity": 1,
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_cart_add_nonexistent_product(client: AsyncClient):
    buyer_data = {**TEST_USER, "email": "cart-no-prod@test.com"}
    await client.post("/api/auth/signup", json=buyer_data)
    login = await client.post("/api/auth/login", json={
        "email": buyer_data["email"],
        "password": buyer_data["password"],
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.post("/api/cart/items", json={
        "product_id": "00000000-0000-0000-0000-000000000000",
        "quantity": 1,
    }, headers=headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_cart_clear(client: AsyncClient):
    buyer_data = {**TEST_USER, "email": "cart-clear@test.com"}
    await client.post("/api/auth/signup", json=buyer_data)
    login = await client.post("/api/auth/login", json={
        "email": buyer_data["email"],
        "password": buyer_data["password"],
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Clear empty cart
    resp = await client.delete("/api/cart", headers=headers)
    assert resp.status_code in (200, 204)
    if resp.status_code == 200:
        assert "items" in resp.json()
