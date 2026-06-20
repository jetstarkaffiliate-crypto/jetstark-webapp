from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.payout import Payout, PayoutStatus
from app.schemas.payout import PayoutRequest, PayoutResponse, PayoutBalanceResponse
from decimal import Decimal

router = APIRouter(prefix="/api/payouts", tags=["Payouts"])


@router.post("", response_model=PayoutResponse, status_code=status.HTTP_201_CREATED)
async def request_payout(
    data: PayoutRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    payout = Payout(
        user_id=current_user.id,
        role=current_user.role.value,
        amount=data.amount,
        bank_name=data.bank_name,
        account_number=data.account_number,
        account_name=data.account_name,
        note=data.note,
    )
    db.add(payout)
    await db.commit()
    await db.refresh(payout)
    return PayoutResponse.model_validate(payout)


@router.get("", response_model=list[PayoutResponse])
async def list_payouts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Payout).where(Payout.user_id == current_user.id).order_by(Payout.requested_at.desc())
    )
    payouts = result.scalars().all()
    return [PayoutResponse.model_validate(p) for p in payouts]


@router.get("/balance", response_model=PayoutBalanceResponse)
async def get_balance(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Total earned from conversions
    from app.models.affiliate import AffiliateConversion
    earn_result = await db.execute(
        select(func.coalesce(func.sum(AffiliateConversion.commission_earned), 0)).where(
            AffiliateConversion.affiliate_id == current_user.id
        )
    )
    total_earned = Decimal(str(earn_result.scalar() or 0))

    # Total paid out
    paid_result = await db.execute(
        select(func.coalesce(func.sum(Payout.amount), 0)).where(
            Payout.user_id == current_user.id,
            Payout.status == PayoutStatus.COMPLETED,
        )
    )
    total_paid = Decimal(str(paid_result.scalar() or 0))

    # Pending payouts
    pending_result = await db.execute(
        select(func.coalesce(func.sum(Payout.amount), 0)).where(
            Payout.user_id == current_user.id,
            Payout.status.in_([PayoutStatus.PENDING, PayoutStatus.PROCESSING]),
        )
    )
    pending = Decimal(str(pending_result.scalar() or 0))

    return PayoutBalanceResponse(
        available_balance=total_earned - total_paid - pending,
        pending_balance=pending,
        total_earned=total_earned,
        total_paid_out=total_paid,
    )
