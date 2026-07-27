from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pathlib import Path
import os
from datetime import datetime, timezone
from app.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.core.notifications import notify_user
from app.models.user import User, UserRole
from app.models.product import Product, ProductStatus
from app.models.order import Order, OrderItem, OrderStatus
from app.models.affiliate import AffiliateLink, AffiliateConversion
from app.schemas.order import OrderCreate, OrderResponse, OrderListResponse, OrderStatusUpdate, OrderItemSchema
from app.schemas.product import ProductResponse
from app.services.email import send_order_confirmation
from decimal import Decimal

router = APIRouter(prefix="/api/orders", tags=["Orders"])

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")


def _build_order_response(order: Order) -> OrderResponse:
    items = []
    for item in order.items:
        has_download = False
        if item.product and item.product.file_path:
            has_download = True
        items.append(OrderItemSchema(
            id=item.id,
            product_id=item.product_id,
            product_name=item.product_name,
            price=item.price,
            quantity=item.quantity,
            vendor_id=item.vendor_id,
            vendor_name=item.vendor_name,
            download_count=item.download_count,
            has_download=has_download,
        ))
    return OrderResponse(
        id=order.id,
        buyer_id=order.buyer_id,
        status=order.status.value if isinstance(order.status, OrderStatus) else order.status,
        subtotal=order.subtotal,
        discount=order.discount,
        total=order.total,
        payment_method=order.payment_method,
        payment_reference=order.payment_reference,
        promo_code=order.promo_code,
        created_at=order.created_at,
        items=items,
    )


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    data: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    subtotal = Decimal("0.00")
    order_items = []

    for item_data in data.items:
        result = await db.execute(select(Product).where(Product.id == item_data.product_id))
        product = result.scalar_one_or_none()
        if not product or product.status != ProductStatus.PUBLISHED:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Product {item_data.product_id} not available")

        item_price = product.price * Decimal(str(item_data.quantity))
        subtotal += item_price

        order_items.append(OrderItem(
            product_id=product.id,
            product_name=product.title,
            price=product.price,
            quantity=item_data.quantity,
            vendor_id=product.vendor_id,
            vendor_name=product.vendor.full_name if product.vendor else None,
        ))

    # Apply promo (placeholder for real promo system)
    discount = Decimal("0.00")
    total = subtotal - discount

    order = Order(
        buyer_id=current_user.id,
        status=OrderStatus.PENDING,
        subtotal=subtotal,
        discount=discount,
        total=total,
        payment_method=data.payment_method,
        buyer_email=data.buyer_email,
        buyer_phone=data.buyer_phone,
        promo_code=data.promo_code,
    )
    db.add(order)
    await db.flush()

    for item in order_items:
        item.order_id = order.id
        db.add(item)

    # Increment sales count
    for item_data in data.items:
        result = await db.execute(select(Product).where(Product.id == item_data.product_id))
        product = result.scalar_one_or_none()
        if product:
            product.sales_count += 1

    # Track affiliate conversion if link code provided
    if data.affiliate_link_code:
        link_result = await db.execute(select(AffiliateLink).where(AffiliateLink.link_code == data.affiliate_link_code))
        aff_link = link_result.scalar_one_or_none()
        if aff_link:
            product_result = await db.execute(select(Product).where(Product.id == aff_link.product_id))
            aff_product = product_result.scalar_one_or_none()
            if aff_product:
                commission = aff_product.price * (aff_product.commission_rate / Decimal("100"))
                conversion = AffiliateConversion(
                    link_id=aff_link.id,
                    affiliate_id=aff_link.affiliate_id,
                    product_id=aff_link.product_id,
                    order_id=order.id,
                    commission_earned=commission,
                )
                db.add(conversion)
                aff_link.conversions += 1
                aff_link.earnings += commission

    await db.commit()
    await db.refresh(order)

    await send_order_confirmation(
        email=data.buyer_email or current_user.email,
        name=current_user.full_name,
        order_id=order.id,
        total=f"{order.total:,.2f}",
    )

    return _build_order_response(order)


@router.get("", response_model=OrderListResponse)
async def list_orders(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Order).where(Order.buyer_id == current_user.id).order_by(Order.created_at.desc())
    )
    orders = result.scalars().all()
    return OrderListResponse(
        orders=[_build_order_response(o) for o in orders],
        total=len(orders),
    )


@router.get("/buyer/stats")
async def buyer_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Order).where(Order.buyer_id == current_user.id)
    )
    orders = result.scalars().all()

    total_orders = len(orders)
    completed_orders = sum(1 for o in orders if o.status == OrderStatus.COMPLETED)
    total_spent = sum(o.total for o in orders if o.status == OrderStatus.COMPLETED)

    digital_items = 0
    for order in orders:
        if order.status == OrderStatus.COMPLETED:
            for item in order.items:
                if item.product and item.product.file_path:
                    digital_items += 1

    return {
        "total_orders": total_orders,
        "completed_orders": completed_orders,
        "total_spent": float(total_spent),
        "digital_purchases": digital_items,
    }


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Order).where(Order.id == order_id, Order.buyer_id == current_user.id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return _build_order_response(order)


@router.get("/{order_id}/items/{item_id}/download")
async def download_item(
    order_id: str,
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Order).where(Order.id == order_id, Order.buyer_id == current_user.id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if order.status != OrderStatus.COMPLETED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order is not completed")

    item = None
    for i in order.items:
        if i.id == item_id:
            item = i
            break
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order item not found")

    if not item.product or not item.product.file_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No file available for this product")

    file_path = Path(UPLOAD_DIR) / "products" / item.product.file_path.lstrip("/")
    if not file_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found on server")

    item.download_count += 1
    item.last_downloaded_at = datetime.now(timezone.utc)
    await db.commit()

    filename = item.product.file_path.split("/")[-1]
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/octet-stream",
    )


@router.get("/admin/all", response_model=OrderListResponse)
async def list_all_orders(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_role(UserRole.ADMIN)),
):
    result = await db.execute(select(Order).order_by(Order.created_at.desc()))
    orders = result.scalars().all()
    return OrderListResponse(
        orders=[_build_order_response(o) for o in orders],
        total=len(orders),
    )


@router.put("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: str,
    data: OrderStatusUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_role(UserRole.ADMIN)),
):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    order.status = OrderStatus(data.status)
    await db.commit()
    await db.refresh(order)

    await notify_user(order.buyer_id, {
        "type": "order_status",
        "order_id": order.id,
        "status": order.status.value,
        "message": f"Your order #{order.id[:8]} is now {order.status.value}",
    })

    return _build_order_response(order)


@router.get("/vendor/earnings")
async def vendor_earnings(
    current_user: User = Depends(require_role(UserRole.VENDOR)),
    db: AsyncSession = Depends(get_db),
):
    completed = await db.execute(
        select(OrderItem)
        .join(Order)
        .where(OrderItem.vendor_id == current_user.id, Order.status == OrderStatus.COMPLETED)
    )
    items = completed.scalars().all()
    total_sales = sum(i.quantity for i in items)
    total_revenue = sum(i.price * Decimal(str(i.quantity)) for i in items)

    pending_count = await db.execute(
        select(func.count(OrderItem.id))
        .join(Order)
        .where(OrderItem.vendor_id == current_user.id, Order.status == OrderStatus.PENDING)
    )
    pending_sales = pending_count.scalar() or 0

    return {
        "total_sales": total_sales,
        "total_revenue": float(total_revenue),
        "completed_orders": len(items),
        "pending_items": pending_sales,
    }
