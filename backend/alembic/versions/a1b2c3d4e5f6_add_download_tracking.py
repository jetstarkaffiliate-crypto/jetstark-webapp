"""add download tracking to order_items

Revision ID: a1b2c3d4e5f6
Revises: f3e1d2c1b0a9
Create Date: 2026-07-26 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f6'
down_revision = 'f3e1d2c1b0a9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('order_items', sa.Column('download_count', sa.Integer(), server_default='0', nullable=False))
    op.add_column('order_items', sa.Column('last_downloaded_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('order_items', 'last_downloaded_at')
    op.drop_column('order_items', 'download_count')
