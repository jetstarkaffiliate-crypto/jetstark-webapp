"""add course_content column to products

Revision ID: f3e1d2c1b0a9
Revises: 530bc26727c3
Create Date: 2026-06-20 12:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "f3e1d2c1b0a9"
down_revision: Union[str, None] = "530bc26727c3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("products", sa.Column("course_content", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("products", "course_content")
