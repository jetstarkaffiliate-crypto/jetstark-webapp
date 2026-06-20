from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field


class AffiliateLinkCreate(BaseModel):
    product_id: str
    label: Optional[str] = None


class AffiliateLinkResponse(BaseModel):
    id: str
    product_id: str
    product_name: Optional[str] = None
    link_code: str
    url: str
    label: Optional[str]
    clicks: int
    conversions: int
    earnings: Decimal
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AffiliateAnalyticsResponse(BaseModel):
    total_clicks: int
    total_conversions: int
    conversion_rate: float
    total_earnings: Decimal
    pending_payout: Decimal
    paid_out: Decimal
    available_balance: Decimal


class AffiliateLinkAnalytics(BaseModel):
    link_id: str
    product_name: str
    clicks: int
    conversions: int
    earnings: Decimal
    conversion_rate: float
