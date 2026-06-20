import hmac, hashlib
import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.order import Order, OrderStatus
from app.config import settings

router = APIRouter(prefix="/api/payments", tags=["Payments"])


@router.post("/initialize")
async def initialize_payment(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not settings.paystack_secret_key:
        raise HTTPException(status_code=501, detail="Payment not configured")

    result = await db.execute(select(Order).where(Order.id == order_id, Order.buyer_id == current_user.id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.paystack.co/transaction/initialize",
            json={
                "email": order.buyer_email,
                "amount": int(order.total * 100),
                "reference": f"JETSTARK_{order.id}",
                "callback_url": f"{settings.cors_origin_list[0]}/orders.html",
            },
            headers={"Authorization": f"Bearer {settings.paystack_secret_key}"},
        )
        data = response.json()
        if not data["status"]:
            raise HTTPException(status_code=400, detail=data.get("message", "Payment initialization failed"))

        order.payment_reference = data["data"]["reference"]
        await db.commit()

        return {"authorization_url": data["data"]["authorization_url"], "reference": data["data"]["reference"]}


@router.post("/verify/{reference}")
async def verify_payment(reference: str, db: AsyncSession = Depends(get_db)):
    if not settings.paystack_secret_key:
        raise HTTPException(status_code=501, detail="Payment not configured")

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.paystack.co/transaction/verify/{reference}",
            headers={"Authorization": f"Bearer {settings.paystack_secret_key}"},
        )
        data = response.json()
        if not data["status"] or data["data"]["status"] != "success":
            raise HTTPException(status_code=400, detail="Payment verification failed")

        result = await db.execute(select(Order).where(Order.payment_reference == reference))
        order = result.scalar_one_or_none()
        if order:
            order.status = OrderStatus.COMPLETED
            await db.commit()

        return {"status": "success", "amount": data["data"]["amount"] / 100}


@router.post("/webhook")
async def paystack_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.body()
    signature = request.headers.get("x-paystack-signature", "")

    if settings.paystack_secret_key:
        expected = hmac.new(
            settings.paystack_secret_key.encode(),
            payload,
            hashlib.sha512,
        ).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise HTTPException(status_code=400, detail="Invalid signature")

    import json
    event = json.loads(payload)
    if event.get("event") == "charge.success":
        reference = event["data"]["reference"]
        result = await db.execute(select(Order).where(Order.payment_reference == reference))
        order = result.scalar_one_or_none()
        if order and order.status != OrderStatus.COMPLETED:
            order.status = OrderStatus.COMPLETED
            order.payment_reference = reference
            await db.commit()

    return {"status": "ok"}
