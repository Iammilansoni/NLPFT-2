"""Add production-ready indexes for templates and metadata

Revision ID: 007
Revises: 006_create_audit_logs
Create Date: 2024-12-01

This migration adds critical indexes for production performance:
- Templates: created_at, updated_at, api_name for sorting and filtering
- Metadata: status, created_at, approved_at for workflow queries
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '007_add_production_indexes'
down_revision = '006_create_audit_logs'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add indexes to templates table for production performance
    op.create_index('idx_templates_created_at', 'templates', ['created_at'], if_not_exists=True)
    op.create_index('idx_templates_updated_at', 'templates', ['updated_at'], if_not_exists=True)
    op.create_index('idx_templates_api_name', 'templates', ['api_name'], if_not_exists=True)
    
    # Add indexes to metadata table for workflow queries
    op.create_index('idx_metadata_status', 'metadata', ['status'], if_not_exists=True)
    op.create_index('idx_metadata_created_at', 'metadata', ['created_at'], if_not_exists=True)
    op.create_index('idx_metadata_approved_at', 'metadata', ['approved_at'], if_not_exists=True)


def downgrade() -> None:
    # Remove indexes from templates table
    op.drop_index('idx_templates_created_at', table_name='templates', if_exists=True)
    op.drop_index('idx_templates_updated_at', table_name='templates', if_exists=True)
    op.drop_index('idx_templates_api_name', table_name='templates', if_exists=True)
    
    # Remove indexes from metadata table
    op.drop_index('idx_metadata_status', table_name='metadata', if_exists=True)
    op.drop_index('idx_metadata_created_at', table_name='metadata', if_exists=True)
    op.drop_index('idx_metadata_approved_at', table_name='metadata', if_exists=True)
