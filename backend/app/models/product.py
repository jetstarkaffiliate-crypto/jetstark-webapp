import enum
import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Text, Numeric, Integer, Boolean, DateTime, Enum, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class ProductStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING = "pending"
    PUBLISHED = "published"
    REJECTED = "rejected"
    SUSPENDED = "suspended"


class Product(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    vendor_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    commission_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=Decimal("20.00"))
    cover_image_url: Mapped[str] = mapped_column(String(512), nullable=True)
    file_path: Mapped[str] = mapped_column(String(512), nullable=True)
    file_size: Mapped[int] = mapped_column(Integer, nullable=True)
    status: Mapped[ProductStatus] = mapped_column(Enum(ProductStatus, values_callable=lambda x: [e.value for e in x]), default=ProductStatus.PENDING)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    rating: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=Decimal("0.00"))
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    sales_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    vendor = relationship("User", back_populates="products", lazy="selectin")
    reviews = relationship("Review", back_populates="product", lazy="selectin")
    order_items = relationship("OrderItem", back_populates="product", lazy="selectin")
    affiliate_links = relationship("AffiliateLink", back_populates="product", lazy="selectin")

    def __repr__(self):
        return f"<Product {self.title} ({self.status.value})>"
