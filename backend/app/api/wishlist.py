from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.product import Product
from app.models.wishlist import Wishlist
from app.schemas.wishlist import WishlistResponse, WishlistItemResponse

router = APIRouter(prefix="/api/wishlist", tags=["Wishlist"])


@router.get("", response_model=WishlistResponse)
async def get_wishlist(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Wishlist).where(Wishlist.user_id == current_user.id).order_by(Wishlist.created_at.desc())
    )
    items = result.scalars().all()
    wishlist_items = []
    for w in items:
        p = w.product
        wishlist_items.append(WishlistItemResponse(
            id=w.id,
            product_id=w.product_id,
            product_name=p.title if p else "Unknown",
            product_price=float(p.price) if p else 0,
            product_image=p.cover_image_url if p else None,
            created_at=w.created_at,
        ))
    return WishlistResponse(items=wishlist_items, total=len(wishlist_items))


@router.post("/products/{product_id}", status_code=status.HTTP_201_CREATED)
async def add_to_wishlist(
    product_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    product_result = await db.execute(select(Product).where(Product.id == product_id))
    if not product_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    existing = await db.execute(
        select(Wishlist).where(Wishlist.user_id == current_user.id, Wishlist.product_id == product_id)
    )
    if existing.scalar_one_or_none():
        return {"message": "Already in wishlist"}

    db.add(Wishlist(user_id=current_user.id, product_id=product_id))
    await db.commit()
    return {"message": "Added to wishlist"}


@router.delete("/products/{product_id}")
async def remove_from_wishlist(
    product_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        delete(Wishlist).where(Wishlist.user_id == current_user.id, Wishlist.product_id == product_id)
    )
    await db.commit()
    return {"message": "Removed from wishlist"}
