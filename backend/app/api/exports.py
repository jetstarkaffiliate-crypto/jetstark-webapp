import csv
import io
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product, ProductStatus
from decimal import Decimal

router = APIRouter(prefix="/api/export", tags=["Export"])


def _generate_csv(rows: list, headers: list) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    output.seek(0)
    return output.getvalue()


@router.get("/orders/csv")
async def export_orders_csv(
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Order).order_by(Order.created_at.desc()))
    orders = result.scalars().all()

    headers = ["Order ID", "Buyer Email", "Status", "Subtotal", "Discount", "Total", "Payment Method", "Created At"]
    rows = []
    for o in orders:
        rows.append([
            o.id[:8],
            o.buyer_email,
            o.status.value if isinstance(o.status, OrderStatus) else o.status,
            str(o.subtotal),
            str(o.discount),
            str(o.total),
            o.payment_method or "",
            o.created_at.strftime("%Y-%m-%d %H:%M") if o.created_at else "",
        ])

    csv_content = _generate_csv(rows, headers)
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=orders.csv"},
    )


@router.get("/orders/csv/my")
async def export_my_orders_csv(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Order).where(Order.buyer_id == current_user.id).order_by(Order.created_at.desc())
    )
    orders = result.scalars().all()

    headers = ["Order ID", "Status", "Subtotal", "Total", "Items", "Created At"]
    rows = []
    for o in orders:
        item_names = ", ".join(i.product_name for i in o.items) if o.items else ""
        rows.append([
            o.id[:8],
            o.status.value if isinstance(o.status, OrderStatus) else o.status,
            str(o.subtotal),
            str(o.total),
            item_names,
            o.created_at.strftime("%Y-%m-%d %H:%M") if o.created_at else "",
        ])

    csv_content = _generate_csv(rows, headers)
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=my-orders.csv"},
    )


@router.get("/products/csv")
async def export_products_csv(
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.VENDOR)),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role == UserRole.VENDOR:
        result = await db.execute(
            select(Product).where(Product.vendor_id == current_user.id).order_by(Product.created_at.desc())
        )
    else:
        result = await db.execute(select(Product).order_by(Product.created_at.desc()))

    products = result.scalars().all()

    headers = ["Product ID", "Title", "Category", "Price", "Commission %", "Status", "Sales", "Rating", "Reviews", "Created At"]
    rows = []
    for p in products:
        rows.append([
            p.id[:8],
            p.title,
            p.category,
            str(p.price),
            str(p.commission_rate),
            p.status.value if isinstance(p.status, ProductStatus) else p.status,
            p.sales_count,
            str(p.rating),
            p.review_count,
            p.created_at.strftime("%Y-%m-%d %H:%M") if p.created_at else "",
        ])

    csv_content = _generate_csv(rows, headers)
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=products.csv"},
    )


@router.get("/earnings/csv")
async def export_earnings_csv(
    current_user: User = Depends(require_role(UserRole.VENDOR)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(OrderItem)
        .join(Order)
        .where(OrderItem.vendor_id == current_user.id, Order.status == OrderStatus.COMPLETED)
        .order_by(Order.created_at.desc())
    )
    items = result.scalars().all()

    headers = ["Order ID", "Product", "Price", "Quantity", "Total", "Buyer", "Date"]
    rows = []
    for item in items:
        rows.append([
            item.order_id[:8],
            item.product_name,
            str(item.price),
            item.quantity,
            str(item.price * Decimal(str(item.quantity))),
            item.order.buyer_email if item.order else "",
            item.order.created_at.strftime("%Y-%m-%d %H:%M") if item.order and item.order.created_at else "",
        ])

    csv_content = _generate_csv(rows, headers)
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=earnings.csv"},
    )
