"""add_endpoint_to_templates

Revision ID: be2c3583c38c
Revises: 098f95a00fb7
Create Date: 2025-12-03 10:25:06.972305+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'be2c3583c38c'
down_revision: Union[str, None] = '098f95a00fb7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add endpoint column to templates table
    op.add_column('templates', sa.Column('endpoint', sa.Text(), nullable=True))


def downgrade() -> None:
    # Remove endpoint column from templates table
    op.drop_column('templates', 'endpoint')
