"""
Database seed script. Run once to populate initial data.
Usage: python -m app.seed
"""
import asyncio
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import select
from app.database import async_session_factory, init_db
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.models.product import Product, ProductStatus


async def seed():
    await init_db()

    async with async_session_factory() as session:
        # Check if already seeded
        result = await session.execute(select(User).limit(1))
        if result.scalar_one_or_none():
            print("Database already seeded. Skipping.")
            return

        admin_id = str(uuid.uuid4())
        vendor_id = str(uuid.uuid4())
        affiliate_id = str(uuid.uuid4())
        buyer_id = str(uuid.uuid4())

        users = [
            User(
                id=admin_id,
                email="admin@jetstark.com",
                password_hash=hash_password("Admin123!"),
                full_name="Admin User",
                role=UserRole.ADMIN,
                is_verified=True,
            ),
            User(
                id=vendor_id,
                email="vendor@jetstark.com",
                password_hash=hash_password("Vendor123!"),
                full_name="Marketing Pro",
                role=UserRole.VENDOR,
                is_verified=True,
            ),
            User(
                id=affiliate_id,
                email="affiliate@jetstark.com",
                password_hash=hash_password("Affiliate123!"),
                full_name="Kunle A.",
                role=UserRole.AFFILIATE,
                is_verified=True,
            ),
            User(
                id=buyer_id,
                email="buyer@jetstark.com",
                password_hash=hash_password("Buyer123!"),
                full_name="Jane Doe",
                role=UserRole.BUYER,
                is_verified=True,
            ),
        ]
        session.add_all(users)

        products = [
            Product(
                id=str(uuid.uuid4()),
                vendor_id=vendor_id,
                title="Digital Marketing Course",
                description="Complete guide to digital marketing. Covers SEO, social media, email marketing, and paid ads.",
                category="Courses",
                price=Decimal("15000.00"),
                commission_rate=Decimal("30.00"),
                status=ProductStatus.PUBLISHED,
                rating=Decimal("4.8"),
                review_count=245,
                sales_count=1250,
            ),
            Product(
                id=str(uuid.uuid4()),
                vendor_id=vendor_id,
                title="Video Editing Templates",
                description="Professional video editing templates for creators. Compatible with Premiere Pro and DaVinci Resolve.",
                category="Templates",
                price=Decimal("5000.00"),
                commission_rate=Decimal("25.00"),
                status=ProductStatus.PUBLISHED,
                rating=Decimal("4.6"),
                review_count=128,
                sales_count=856,
            ),
            Product(
                id=str(uuid.uuid4()),
                vendor_id=vendor_id,
                title="AI Content Planner",
                description="A premium planner for digital creators. Plan content, track trends, and automate publishing.",
                category="Tools",
                price=Decimal("12000.00"),
                commission_rate=Decimal("35.00"),
                status=ProductStatus.PENDING,
                rating=Decimal("0"),
                review_count=0,
                sales_count=0,
            ),
        ]
        session.add_all(products)

        await session.commit()

        print("Database seeded successfully!")
        print(f"  Admin:     admin@jetstark.com / Admin123!")
        print(f"  Vendor:    vendor@jetstark.com / Vendor123!")
        print(f"  Affiliate: affiliate@jetstark.com / Affiliate123!")
        print(f"  Buyer:     buyer@jetstark.com / Buyer123!")


if __name__ == "__main__":
    asyncio.run(seed())
