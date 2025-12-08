"""create audit_logs table

Revision ID: 006_create_audit_logs
Revises: 005_add_is_expert_to_users
Create Date: 2025-11-15

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision = '006_create_audit_logs'
down_revision = '005_add_is_expert_to_users'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create audit_logs table for tracking user actions
    op.create_table(
        'audit_logs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', UUID(as_uuid=True), nullable=True),  # Nullable for system actions
        sa.Column('action', sa.Text(), nullable=False),  # CREATE, UPDATE, DELETE, LOGIN, LOGOUT, etc.
        sa.Column('table_name', sa.Text(), nullable=True),  # Table affected (templates, datasets, etc.)
        sa.Column('record_id', UUID(as_uuid=True), nullable=True),  # ID of affected record
        sa.Column('old_data', JSONB, nullable=True),  # Previous state (for UPDATE/DELETE)
        sa.Column('new_data', JSONB, nullable=True),  # New state (for CREATE/UPDATE)
        sa.Column('ip_address', sa.Text(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('request_method', sa.Text(), nullable=True),  # GET, POST, PUT, DELETE
        sa.Column('request_path', sa.Text(), nullable=True),  # API endpoint
        sa.Column('status_code', sa.Integer(), nullable=True),  # HTTP status code
        sa.Column('error_message', sa.Text(), nullable=True),  # Error if failed
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('NOW()')),
    )
    
    # Create indexes for common queries
    op.create_index('idx_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('idx_audit_logs_created_at', 'audit_logs', ['created_at'], postgresql_using='btree')
    op.create_index('idx_audit_logs_table_record', 'audit_logs', ['table_name', 'record_id'])
    op.create_index('idx_audit_logs_action', 'audit_logs', ['action'])
    
    # Add foreign key to users table (with ON DELETE SET NULL for orphaned logs)
    op.create_foreign_key(
        'fk_audit_logs_user_id',
        'audit_logs', 'users',
        ['user_id'], ['user_id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    op.drop_constraint('fk_audit_logs_user_id', 'audit_logs', type_='foreignkey')
    op.drop_index('idx_audit_logs_action', table_name='audit_logs')
    op.drop_index('idx_audit_logs_table_record', table_name='audit_logs')
    op.drop_index('idx_audit_logs_created_at', table_name='audit_logs')
    op.drop_index('idx_audit_logs_user_id', table_name='audit_logs')
    op.drop_table('audit_logs')
