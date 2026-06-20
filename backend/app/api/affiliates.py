import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.product import Product
from app.models.affiliate import AffiliateLink, AffiliateClick, AffiliateConversion
from app.models.order import Order
from app.schemas.affiliate import (
    AffiliateLinkCreate, AffiliateLinkResponse,
    AffiliateAnalyticsResponse, AffiliateLinkAnalytics,
)
from decimal import Decimal

router = APIRouter(prefix="/api/affiliate", tags=["Affiliate"])


@router.post("/track-click")
async def track_click(
    link_code: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(AffiliateLink).where(AffiliateLink.link_code == link_code))
    link = result.scalar_one_or_none()
    if not link:
        return {"status": "ok"}
    link.clicks += 1
    click = AffiliateClick(
        link_id=link.id,
        affiliate_id=link.affiliate_id,
        product_id=link.product_id,
    )
    db.add(click)
    await db.commit()
    return {"status": "ok"}


@router.post("/links", response_model=AffiliateLinkResponse, status_code=status.HTTP_201_CREATED)
async def create_affiliate_link(
    data: AffiliateLinkCreate,
    current_user: User = Depends(require_role(UserRole.AFFILIATE)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Product).where(Product.id == data.product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    link_code = uuid.uuid4().hex[:10]
    link = AffiliateLink(
        affiliate_id=current_user.id,
        product_id=data.product_id,
        link_code=link_code,
        label=data.label or product.title,
    )
    db.add(link)
    await db.commit()
    await db.refresh(link)

    return AffiliateLinkResponse(
        id=link.id,
        product_id=link.product_id,
        product_name=product.title,
        link_code=link.link_code,
        url=f"/product-detail.html?id={link.product_id}&ref={link.affiliate_id}&link={link.link_code}",
        label=link.label,
        clicks=link.clicks,
        conversions=link.conversions,
        earnings=link.earnings,
        is_active=link.is_active,
        created_at=link.created_at,
    )


@router.get("/links", response_model=list[AffiliateLinkResponse])
async def list_affiliate_links(
    current_user: User = Depends(require_role(UserRole.AFFILIATE)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AffiliateLink).where(
            AffiliateLink.affiliate_id == current_user.id,
            AffiliateLink.is_active == True,
        ).order_by(AffiliateLink.created_at.desc())
    )
    links = result.scalars().all()

    responses = []
    for link in links:
        product_name = link.product.title if link.product else None
        responses.append(AffiliateLinkResponse(
            id=link.id,
            product_id=link.product_id,
            product_name=product_name,
            link_code=link.link_code,
            url=f"/product-detail.html?id={link.product_id}&ref={link.affiliate_id}&link={link.link_code}",
            label=link.label,
            clicks=link.clicks,
            conversions=link.conversions,
            earnings=link.earnings,
            is_active=link.is_active,
            created_at=link.created_at,
        ))
    return responses


@router.delete("/links/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_affiliate_link(
    link_id: str,
    current_user: User = Depends(require_role(UserRole.AFFILIATE)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AffiliateLink).where(AffiliateLink.id == link_id, AffiliateLink.affiliate_id == current_user.id)
    )
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    link.is_active = False
    await db.commit()


@router.get("/analytics", response_model=AffiliateAnalyticsResponse)
async def get_analytics(
    current_user: User = Depends(require_role(UserRole.AFFILIATE)),
    db: AsyncSession = Depends(get_db),
):
    # Total clicks
    click_result = await db.execute(
        select(func.count(AffiliateClick.id)).where(AffiliateClick.affiliate_id == current_user.id)
    )
    total_clicks = click_result.scalar() or 0

    # Total conversions
    conv_result = await db.execute(
        select(func.count(AffiliateConversion.id)).where(AffiliateConversion.affiliate_id == current_user.id)
    )
    total_conversions = conv_result.scalar() or 0

    # Total earnings
    earn_result = await db.execute(
        select(func.coalesce(func.sum(AffiliateConversion.commission_earned), 0)).where(
            AffiliateConversion.affiliate_id == current_user.id
        )
    )
    total_earnings = Decimal(str(earn_result.scalar() or 0))

    conversion_rate = (total_conversions / total_clicks * 100) if total_clicks > 0 else 0

    return AffiliateAnalyticsResponse(
        total_clicks=total_clicks,
        total_conversions=total_conversions,
        conversion_rate=round(conversion_rate, 2),
        total_earnings=total_earnings,
        pending_payout=total_earnings * Decimal("0.7"),
        paid_out=Decimal("0"),
        available_balance=total_earnings,
    )
