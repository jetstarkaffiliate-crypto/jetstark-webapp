from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.product import Product, ProductStatus
from app.models.cart import Cart, CartItem
from app.schemas.cart import CartResponse, CartItemCreate, CartItemUpdate, CartItemResponse
from decimal import Decimal

router = APIRouter(prefix="/api/cart", tags=["Cart"])


async def get_or_create_cart(user_id: str, db: AsyncSession) -> Cart:
    result = await db.execute(select(Cart).where(Cart.user_id == user_id))
    cart = result.scalar_one_or_none()
    if not cart:
        cart = Cart(user_id=user_id)
        db.add(cart)
        await db.commit()
        await db.refresh(cart)
    return cart


async def build_cart_response(cart: Cart) -> CartResponse:
    items = []
    total = Decimal("0.00")
    for item in cart.items:
        product = item.product
        items.append(CartItemResponse(
            id=item.id,
            product_id=item.product_id,
            product_name=product.title if product else "Unknown",
            product_price=product.price if product else Decimal("0"),
            product_image=product.cover_image_url if product else None,
            quantity=item.quantity,
        ))
        if product:
            total += product.price * Decimal(str(item.quantity))
    return CartResponse(
        id=cart.id,
        items=items,
        total=total,
        item_count=sum(i.quantity for i in cart.items),
        created_at=cart.created_at,
        updated_at=cart.updated_at,
    )


@router.get("", response_model=CartResponse)
async def get_cart(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cart = await get_or_create_cart(current_user.id, db)
    return await build_cart_response(cart)


@router.post("/items", response_model=CartResponse, status_code=status.HTTP_201_CREATED)
async def add_to_cart(
    data: CartItemCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    product_result = await db.execute(
        select(Product).where(Product.id == data.product_id, Product.status == ProductStatus.PUBLISHED)
    )
    product = product_result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    cart = await get_or_create_cart(current_user.id, db)

    existing = [i for i in cart.items if i.product_id == data.product_id]
    if existing:
        existing[0].quantity += data.quantity
    else:
        cart.items.append(CartItem(
            cart_id=cart.id,
            product_id=data.product_id,
            quantity=data.quantity,
        ))

    await db.commit()
    await db.refresh(cart)
    return await build_cart_response(cart)


@router.put("/items/{item_id}", response_model=CartResponse)
async def update_cart_item(
    item_id: str,
    data: CartItemUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(CartItem).where(CartItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")

    cart = await get_or_create_cart(current_user.id, db)
    if item.cart_id != cart.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your cart item")

    item.quantity = data.quantity
    await db.commit()
    await db.refresh(cart)
    return await build_cart_response(cart)


@router.delete("/items/{item_id}", response_model=CartResponse)
async def remove_cart_item(
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(CartItem).where(CartItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")

    cart = await get_or_create_cart(current_user.id, db)
    if item.cart_id != cart.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your cart item")

    await db.delete(item)
    await db.commit()
    await db.refresh(cart)
    return await build_cart_response(cart)


@router.delete("", response_model=CartResponse)
async def clear_cart(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cart = await get_or_create_cart(current_user.id, db)
    for item in cart.items:
        await db.delete(item)
    await db.commit()
    await db.refresh(cart)
    return await build_cart_response(cart)
