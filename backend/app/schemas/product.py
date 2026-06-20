from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1, max_length=5000)
    category: str = Field(min_length=1, max_length=100)
    price: Decimal = Field(gt=0, le=9999999.99)
    commission_rate: Decimal = Field(ge=0, le=100, default=Decimal("20.00"))
    cover_image_url: Optional[str] = None


class ProductUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    category: Optional[str] = None
    price: Optional[Decimal] = Field(None, gt=0)
    commission_rate: Optional[Decimal] = Field(None, ge=0, le=100)


class ProductResponse(BaseModel):
    id: str
    vendor_id: str
    title: str
    description: str
    category: str
    price: Decimal
    commission_rate: Decimal
    cover_image_url: Optional[str]
    status: str
    is_featured: bool
    rating: Decimal
    review_count: int
    sales_count: int
    vendor_name: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ProductListResponse(BaseModel):
    products: List[ProductResponse]
    total: int
    page: int
    page_size: int
