"""add template sample_requests and domain_tags

Revision ID: 003
Revises: 002
Create Date: 2024-11-14

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add sample_requests column (JSONB array of sample requests)
    op.add_column('templates', sa.Column('sample_requests', JSONB, nullable=True))
    
    # Add domain_tags column (JSONB array of domain/context tags)
    op.add_column('templates', sa.Column('domain_tags', JSONB, nullable=True))

def downgrade() -> None:
    # Drop columns
    op.drop_column('templates', 'domain_tags')
    op.drop_column('templates', 'sample_requests')
