"""initial schema

Revision ID: 530bc26727c3
Revises:
Create Date: 2026-06-20 11:46:44.274393
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "530bc26727c3"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column(
            "role",
            sa.Enum("buyer", "affiliate", "vendor", "admin", name="userrole"),
            nullable=False,
            server_default="buyer",
        ),
        sa.Column("is_verified", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("two_factor_enabled", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("two_factor_secret", sa.String(64), nullable=True),
        sa.Column("profile_picture_url", sa.String(512), nullable=True),
        sa.Column("bio", sa.String(1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "products",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("vendor_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("commission_rate", sa.Numeric(5, 2), nullable=False, server_default=sa.text("20.00")),
        sa.Column("cover_image_url", sa.String(512), nullable=True),
        sa.Column("file_path", sa.String(512), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("draft", "pending", "published", "rejected", "suspended", name="productstatus"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("is_featured", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("rating", sa.Numeric(3, 2), server_default=sa.text("0.00"), nullable=False),
        sa.Column("review_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("sales_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "orders",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("buyer_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "processing", "completed", "failed", "refunded", name="orderstatus"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("subtotal", sa.Numeric(10, 2), nullable=False),
        sa.Column("discount", sa.Numeric(10, 2), server_default=sa.text("0.00"), nullable=False),
        sa.Column("total", sa.Numeric(10, 2), nullable=False),
        sa.Column("payment_method", sa.String(50), nullable=True),
        sa.Column("payment_reference", sa.String(255), nullable=True),
        sa.Column("promo_code", sa.String(50), nullable=True),
        sa.Column("buyer_email", sa.String(255), nullable=False),
        sa.Column("buyer_phone", sa.String(20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "order_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("order_id", sa.String(36), sa.ForeignKey("orders.id"), nullable=False),
        sa.Column("product_id", sa.String(36), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("product_name", sa.String(255), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("quantity", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("vendor_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("vendor_name", sa.String(255), nullable=True),
    )

    op.create_table(
        "affiliate_links",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("affiliate_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("product_id", sa.String(36), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("link_code", sa.String(50), unique=True, nullable=False, index=True),
        sa.Column("label", sa.String(255), nullable=True),
        sa.Column("clicks", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("conversions", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("earnings", sa.Numeric(10, 2), server_default=sa.text("0.00"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expired_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "affiliate_clicks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("link_id", sa.String(36), sa.ForeignKey("affiliate_links.id"), nullable=False),
        sa.Column("affiliate_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("product_id", sa.String(36), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("referrer", sa.String(512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "affiliate_conversions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("link_id", sa.String(36), sa.ForeignKey("affiliate_links.id"), nullable=False),
        sa.Column("affiliate_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("product_id", sa.String(36), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("order_id", sa.String(36), sa.ForeignKey("orders.id"), nullable=False),
        sa.Column("commission_earned", sa.Numeric(10, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "payouts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("fee", sa.Numeric(10, 2), server_default=sa.text("0.00"), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "processing", "completed", "failed", "cancelled", name="payoutstatus"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("payment_method", sa.String(50), server_default=sa.text("'bank_transfer'"), nullable=False),
        sa.Column("bank_name", sa.String(255), nullable=True),
        sa.Column("account_number", sa.String(20), nullable=True),
        sa.Column("account_name", sa.String(255), nullable=True),
        sa.Column("transaction_reference", sa.String(255), nullable=True),
        sa.Column("note", sa.String(500), nullable=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "reviews",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("product_id", sa.String(36), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("is_verified_purchase", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("is_approved", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("token", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "carts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), unique=True, nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "cart_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("cart_id", sa.String(36), sa.ForeignKey("carts.id"), nullable=False, index=True),
        sa.Column("product_id", sa.String(36), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("quantity", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "wishlists",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("product_id", sa.String(36), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "product_id", name="uq_user_product_wishlist"),
    )


def downgrade() -> None:
    op.drop_table("wishlists")
    op.drop_table("cart_items")
    op.drop_table("carts")
    op.drop_table("password_reset_tokens")
    op.drop_table("reviews")
    op.drop_table("payouts")
    op.drop_table("affiliate_conversions")
    op.drop_table("affiliate_clicks")
    op.drop_table("affiliate_links")
    op.drop_table("order_items")
    op.drop_table("orders")
    op.drop_table("products")
    op.drop_table("users")

    op.execute("DROP TYPE IF EXISTS userrole")
    op.execute("DROP TYPE IF EXISTS productstatus")
    op.execute("DROP TYPE IF EXISTS orderstatus")
    op.execute("DROP TYPE IF EXISTS payoutstatus")
