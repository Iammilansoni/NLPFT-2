"""add email verification table

Revision ID: add_email_verification
Revises: 
Create Date: 2025-11-15

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '007_add_email_verification'
down_revision = '006_create_audit_logs'  # Link to migration 006
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create email_verification table
    op.create_table(
        'email_verification',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('email', sa.Text(), nullable=False),
        sa.Column('otp', sa.Text(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('expires_at', sa.TIMESTAMP(), nullable=False),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('attempts', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('ip_address', sa.Text(), nullable=True),
    )
    
    # Create index on email for faster lookups
    op.create_index('ix_email_verification_email', 'email_verification', ['email'])


def downgrade() -> None:
    op.drop_index('ix_email_verification_email', table_name='email_verification')
    op.drop_table('email_verification')
