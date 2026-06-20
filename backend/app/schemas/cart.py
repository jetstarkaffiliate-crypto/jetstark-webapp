from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field


class CartItemCreate(BaseModel):
    product_id: str
    quantity: int = Field(default=1, ge=1)


class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=1)


class CartItemResponse(BaseModel):
    id: str
    product_id: str
    product_name: str
    product_price: Decimal
    product_image: Optional[str] = None
    quantity: int

    model_config = {"from_attributes": True}


class CartResponse(BaseModel):
    id: str
    items: List[CartItemResponse]
    total: Decimal
    item_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
