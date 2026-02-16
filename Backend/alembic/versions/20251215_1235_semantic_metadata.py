"""Add semantic retrieval metadata to csv_data

Revision ID: 20251215_1235_semantic_metadata
Revises: 20251212_0946_22b9ae9886b8
Create Date: 2025-12-15

Adds intent_type, simulate, and confidence_score fields to csv_data table
for the semantic API retrieval pipeline.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251215_1235_semantic_metadata'
down_revision = '22b9ae9886b8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add semantic retrieval metadata columns to csv_data table."""
    # Add intent_type column
    op.add_column(
        'csv_data',
        sa.Column('intent_type', sa.Text(), nullable=True,
                  comment='Query intent: create, read, update, delete, query, unknown')
    )
    
    # Add simulate column (0=no, 1=yes)
    op.add_column(
        'csv_data',
        sa.Column('simulate', sa.Integer(), nullable=False, server_default='0',
                  comment='Whether to simulate API call: 0=no (real), 1=yes (mock)')
    )
    
    # Add confidence_score column
    op.add_column(
        'csv_data',
        sa.Column('confidence_score', sa.Numeric(), nullable=True,
                  comment='Confidence score for this query: 0.0 to 1.0')
    )
    
    # Add index on intent_type for filtering
    op.create_index(
        'idx_csv_data_intent_type',
        'csv_data',
        ['intent_type']
    )


def downgrade() -> None:
    """Remove semantic retrieval metadata columns from csv_data table."""
    op.drop_index('idx_csv_data_intent_type', table_name='csv_data')
    op.drop_column('csv_data', 'confidence_score')
    op.drop_column('csv_data', 'simulate')
    op.drop_column('csv_data', 'intent_type')
