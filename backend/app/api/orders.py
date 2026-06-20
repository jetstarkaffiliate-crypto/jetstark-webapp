from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.product import Product, ProductStatus
from app.models.order import Order, OrderItem, OrderStatus
from app.models.affiliate import AffiliateLink, AffiliateConversion
from app.schemas.order import OrderCreate, OrderResponse, OrderListResponse, OrderStatusUpdate
from app.schemas.product import ProductResponse
from app.services.email import send_order_confirmation
from decimal import Decimal

router = APIRouter(prefix="/api/orders", tags=["Orders"])


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

    return OrderResponse.model_validate(order)


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
        orders=[OrderResponse.model_validate(o) for o in orders],
        total=len(orders),
    )


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
    return OrderResponse.model_validate(order)


@router.get("/admin/all", response_model=OrderListResponse)
async def list_all_orders(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_role(UserRole.ADMIN)),
):
    result = await db.execute(select(Order).order_by(Order.created_at.desc()))
    orders = result.scalars().all()
    return OrderListResponse(
        orders=[OrderResponse.model_validate(o) for o in orders],
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
    return OrderResponse.model_validate(order)


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
