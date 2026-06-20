from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.product import Product
from app.models.review import Review
from app.schemas.review import ReviewCreate, ReviewResponse, ReviewListResponse
from decimal import Decimal

router = APIRouter(prefix="/api/reviews", tags=["Reviews"])


@router.post("/products/{product_id}", response_model=ReviewResponse, status_code=201)
async def create_review(
    product_id: str,
    data: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    review = Review(
        product_id=product_id,
        user_id=current_user.id,
        rating=data.rating,
        comment=data.comment,
    )
    db.add(review)

    # Update product rating
    avg_result = await db.execute(
        select(func.avg(Review.rating)).where(Review.product_id == product_id, Review.is_approved == True)
    )
    avg_rating = avg_result.scalar()
    count_result = await db.execute(
        select(func.count(Review.id)).where(Review.product_id == product_id, Review.is_approved == True)
    )
    review_count = count_result.scalar() or 0

    product.rating = Decimal(str(round(avg_rating or data.rating, 2)))
    product.review_count = review_count + 1

    await db.commit()
    await db.refresh(review)

    return ReviewResponse(
        id=review.id,
        product_id=review.product_id,
        user_id=review.user_id,
        user_name=current_user.full_name,
        rating=review.rating,
        comment=review.comment,
        is_verified_purchase=review.is_verified_purchase,
        created_at=review.created_at,
    )


@router.get("/products/{product_id}", response_model=ReviewListResponse)
async def get_product_reviews(product_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Review).where(
            Review.product_id == product_id,
            Review.is_approved == True,
        ).order_by(Review.created_at.desc())
    )
    reviews = result.scalars().all()

    avg_result = await db.execute(
        select(func.avg(Review.rating)).where(Review.product_id == product_id, Review.is_approved == True)
    )
    avg_rating = float(avg_result.scalar() or 0)

    review_responses = []
    for r in reviews:
        review_responses.append(ReviewResponse(
            id=r.id,
            product_id=r.product_id,
            user_id=r.user_id,
            user_name=r.user.full_name if r.user else None,
            rating=r.rating,
            comment=r.comment,
            is_verified_purchase=r.is_verified_purchase,
            created_at=r.created_at,
        ))

    return ReviewListResponse(
        reviews=review_responses,
        total=len(review_responses),
        average_rating=round(avg_rating, 2),
    )
