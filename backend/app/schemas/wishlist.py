from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class WishlistItemResponse(BaseModel):
    id: str
    product_id: str
    product_name: str
    product_price: float
    product_image: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class WishlistResponse(BaseModel):
    items: List[WishlistItemResponse]
    total: int
