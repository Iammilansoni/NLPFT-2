"""Remove simulate column from csv_data

Revision ID: 20251215_1400_remove_simulate
Revises: 20251215_1235_semantic_metadata
Create Date: 2025-12-15

Removes the simulate field as it's no longer needed in the schema.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251215_1400_remove_simulate'
down_revision = '20251215_1235_semantic_metadata'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Remove simulate column from csv_data table."""
    op.drop_column('csv_data', 'simulate')


def downgrade() -> None:
    """Re-add simulate column to csv_data table."""
    op.add_column(
        'csv_data',
        sa.Column('simulate', sa.Integer(), nullable=False, server_default='0',
                  comment='Whether to simulate API call: 0=no (real), 1=yes (mock)')
    )
