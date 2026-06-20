from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=2000)


class ReviewResponse(BaseModel):
    id: str
    product_id: str
    user_id: str
    user_name: Optional[str] = None
    rating: int
    comment: Optional[str]
    is_verified_purchase: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ReviewListResponse(BaseModel):
    reviews: List[ReviewResponse]
    total: int
    average_rating: float
