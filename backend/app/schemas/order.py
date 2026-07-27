from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field


class OrderItemSchema(BaseModel):
    id: Optional[str] = None
    product_id: str
    product_name: str
    price: Decimal
    quantity: int = 1
    vendor_id: Optional[str] = None
    vendor_name: Optional[str] = None
    download_count: int = 0
    has_download: bool = False

    model_config = {"from_attributes": True}


class OrderCreate(BaseModel):
    items: List[OrderItemSchema]
    buyer_email: str
    buyer_phone: Optional[str] = None
    promo_code: Optional[str] = None
    payment_method: str = "paystack"
    affiliate_ref: Optional[str] = None
    affiliate_link_code: Optional[str] = None


class OrderResponse(BaseModel):
    id: str
    buyer_id: str
    status: str
    subtotal: Decimal
    discount: Decimal
    total: Decimal
    payment_method: Optional[str]
    payment_reference: Optional[str]
    promo_code: Optional[str]
    created_at: datetime
    items: List[OrderItemSchema]

    model_config = {"from_attributes": True}


class OrderListResponse(BaseModel):
    orders: List[OrderResponse]
    total: int


class OrderStatusUpdate(BaseModel):
    status: str = Field(pattern=r"^(pending|processing|completed|failed|refunded)$")
