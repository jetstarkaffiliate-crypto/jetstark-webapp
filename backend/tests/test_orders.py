import pytest
from httpx import AsyncClient
from tests.fixtures.data import TEST_USER


@pytest.mark.asyncio
async def test_list_orders(client: AsyncClient):
    """Test that a buyer can list their orders (empty list)."""
    buyer_data = {**TEST_USER, "email": "order-list@test.com"}
    await client.post("/api/auth/signup", json=buyer_data)
    login = await client.post("/api/auth/login", json={
        "email": buyer_data["email"],
        "password": buyer_data["password"],
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.get("/api/orders", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "orders" in data


@pytest.mark.asyncio
async def test_create_order_unauthenticated(client: AsyncClient):
    resp = await client.post("/api/orders", json={
        "items": [],
        "buyer_email": "test@test.com",
        "buyer_phone": "+2348000000000",
        "payment_method": "paystack",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_order_status_update_requires_admin(client: AsyncClient):
    buyer_data = {**TEST_USER, "email": "order-status@test.com"}
    await client.post("/api/auth/signup", json=buyer_data)
    login = await client.post("/api/auth/login", json={
        "email": buyer_data["email"],
        "password": buyer_data["password"],
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.put("/api/orders/fake-id/status", json={"status": "processing"}, headers=headers)
    assert resp.status_code == 403
