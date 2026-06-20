from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.core.dependencies import require_role
from app.models.user import User, UserRole
from app.models.product import Product, ProductStatus
from app.models.order import Order, OrderStatus
from decimal import Decimal

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/stats")
async def admin_stats(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_role(UserRole.ADMIN)),
):
    user_count = await db.execute(select(func.count(User.id)))
    product_count = await db.execute(select(func.count(Product.id)))
    pending_product_count = await db.execute(
        select(func.count(Product.id)).where(Product.status == ProductStatus.PENDING)
    )
    order_count = await db.execute(select(func.count(Order.id)))
    revenue_result = await db.execute(
        select(func.coalesce(func.sum(Order.total), 0)).where(Order.status == OrderStatus.COMPLETED)
    )

    return {
        "total_users": user_count.scalar() or 0,
        "total_products": product_count.scalar() or 0,
        "pending_products": pending_product_count.scalar() or 0,
        "total_orders": order_count.scalar() or 0,
        "total_revenue": float(revenue_result.scalar() or 0),
    }
